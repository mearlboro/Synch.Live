"""
Simple class implementing a running calculator for the quantities related to
the PhiID theory of causal emergence, as described in:

Rosas FE*, Mediano PAM*, Jensen HJ, Seth AK, Barrett AB, Carhart-Harris RL, et
al. (2020) Reconciling emergences: An information-theoretic approach to
identify causal emergence in multivariate data. PLoS Comput Biol 16(12):
e1008289.

Pedro Mediano, Oct 2021
"""

import click
import jpype as jp
import logging
import numpy as np
import os

from typing import Callable, Iterable

# initialise logging to file
import synch_live.camera.core.logger

INFODYNAMICS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'infodynamics.jar')
SAMPLE_THRESHOLD = 180
PSI_START = -5

def javify(Xi: np.ndarray) -> jp.JArray:
    """
    Convert a numpy array into a Java array to pass to the JIDT classes and
    functions.
    Given a 1-dimensional np array of shape (D,)  , return Java array of size D
    Given a 2-dimensional np array of shape (1, D), return Java array of size D

    Params
    ------
    Xi
        numpy array of shape (D,) or (1,D) representing one 'micro' part of the
        system or one value of the macroscopic feature

    Returns
    ------
    jXi
        the Xi array cast to Java Array
    """
    if len(Xi.shape) == 1:
        D = Xi.shape[0]
        Xi = Xi[np.newaxis, :]
        jXi = jp.JArray(jp.JDouble, D)(Xi.tolist())
    else:
        D = Xi.shape[1]
        jXi = jp.JArray(jp.JDouble, D)(Xi.tolist())

    return jXi


def compute_macro(X: Iterable[np.ndarray]) -> np.ndarray:
    """
    Computes a supervenient macroscopic feature.

    Params
    ------
    X : iter of np.ndarray
        each element of X contains a 1D numpy array of shape (1,T) representing one
        'micro' part of the system.

    Returns
    -------
    V
        Macroscopic feature of interest of D-dimensions of shape (1,D)
    """
    V = np.mean(X, axis = 0)

    return V[np.newaxis, :]


class EmergenceCalculator():
    def __init__(self,
            macro_fun: Callable[[np.ndarray], np.ndarray],
            use_correction: bool = True,
            psi_buffer_size : int = 60,
            observation_window_size : int = 120,
            use_local : bool = False
        ) -> None:
        """
        Construct the emergence calculator by setting member variables and
        checking the JVM is started. The JIDT calculators will be initialised
        later, when the first batch of data is provided.

        After calculating the value of emergence for a given frame, it is
        median-filtered with recent past values to reduce volatility.

        Parameters
        ----------
        macro_fun: Callable
            a function that takes an iter of numpy arrays of the same shape (1,T)
            and returns a numpy array of shape (1,D)
        use_correction : bool
            Whether to use the 1st-order lattice correction for emergence
            calculation.
        psi_buffer_size : int
            Number of past emergence values used for the median filter
            (default: 12).
        observation_window_size : int
            Number of past observations to take into account for the calculation
            of psi. If negative or zero, use all past data (default: -1).
        use_local : bool
            If true, computes psi the local (i.e. pointwise) mutual info of
            the latest sample. If false, uses the standard (i.e. average) mutual
            info of the observation window (Default: true).
        """

        self.is_initialised = False
        self.sample_counter = 0

        self.use_correction = use_correction
        self.psi_buffer_size = psi_buffer_size
        self.past_psi_vals = [PSI_START] * psi_buffer_size

        self.observation_window_size = observation_window_size
        self.observations_V = []
        self.observations_X = []

        self.use_local = use_local

        self.compute_macro = macro_fun

        if not jp.isJVMStarted():
            logging.info('Starting JVM...')
            jp.startJVM(jp.getDefaultJVMPath(), '-ea', '-Djava.class.path=%s'%INFODYNAMICS_PATH)
            logging.info('JVM started using jpype1')

        logging.info('Successfully initialised EmergenceCalculator with buffer {psi_buffer_size} and observation window {observation_window_size}.')


    def initialise_calculators(self, X: np.ndarray, V: np.ndarray) -> None:
        """
        """
        self.N = len(X)

        self.xmiCalcs = []
        for Xi in X:
            Xi = Xi[np.newaxis, :]
            self.xmiCalcs.append(jp.JClass('infodynamics.measures.continuous.gaussian.MutualInfoCalculatorMultiVariateGaussian')())
            self.xmiCalcs[-1].initialise(Xi.shape[1], V.shape[1])
            self.xmiCalcs[-1].startAddObservations()

        self.vmiCalc = jp.JClass('infodynamics.measures.continuous.gaussian.MutualInfoCalculatorMultiVariateGaussian')()
        self.vmiCalc.initialise(V.shape[1], V.shape[1])
        self.vmiCalc.startAddObservations()

        self.is_initialised = True


    def update_calculators(self, V: np.ndarray) -> None:
        """
        """
        jV = javify(V)
        jVp = javify(self.past_V)
        jXp = [javify(Xip) for Xip in self.past_X]

        if self.observation_window_size <= 0:
            self.vmiCalc.addObservations(jVp, jV)
            for jXip,calc in zip(jXp, self.xmiCalcs):
                calc.addObservations(jXip, jV)

        else:
            self.observations_V.append((jVp, jV))
            self.observations_X.append((jXp, jV))
            if len(self.observations_V) > self.observation_window_size:
                self.observations_V.pop(0)
                self.observations_X.pop(0)

            self.initialise_calculators(self.past_X, V)
            for jVp, jV in self.observations_V:
                self.vmiCalc.addObservations(jVp, jV)
            for jXp, jV in self.observations_X:
                for jXip,calc in zip(jXp, self.xmiCalcs):
                    calc.addObservations(jXip, jV)


    def compute_psi(self, V: np.ndarray) -> float:
        """
        """
        self.vmiCalc.finaliseAddObservations()
        jV = javify(V)

        if self.use_local:
            psi = self.vmiCalc.computeLocalUsingPreviousObservations(
                    javify(self.past_V), jV)[0]
            for Xip,calc in zip(self.past_X, self.xmiCalcs):
                calc.finaliseAddObservations()
                psi -= calc.computeLocalUsingPreviousObservations(javify(Xip), jV)[0]

            if self.use_correction:
                marginal_mi = [ calc.computeAverageLocalOfObservations()
                                for calc in self.xmiCalcs ]
                psi += (self.N - 1) * np.min(marginal_mi)

        else:
            psi = self.vmiCalc.computeAverageLocalOfObservations()
            for calc in self.xmiCalcs:
                calc.finaliseAddObservations()
                psi -= calc.computeAverageLocalOfObservations()

            if self.use_correction:
                marginal_mi = [ calc.computeAverageLocalOfObservations()
                                for calc in self.xmiCalcs ]
                psi += (self.N - 1) * np.min(marginal_mi)

        return psi


    def update_and_compute(self, X: Iterable[np.ndarray]) -> float:
        """
        """
        V = self.compute_macro(X)

        psi = PSI_START
        if not self.is_initialised:
            self.initialise_calculators(X, V)

        else:
            self.update_calculators(V)
            if self.sample_counter > SAMPLE_THRESHOLD:
                psi = self.compute_psi(V)

        self.past_X = X
        self.past_V = V
        self.sample_counter += 1

        self.past_psi_vals.append(psi)
        if len(self.past_psi_vals) > self.psi_buffer_size:
            self.past_psi_vals.pop(0)
        psi_filt = np.nanmedian(self.past_psi_vals)

        logging.info(f'Unfiltered Psi {self.sample_counter}: {psi}')
        logging.info(f'Filtered Psi {self.sample_counter}: {psi_filt}')

        return psi_filt


    def exit(self) -> None:
        """
        Gracefully shut down JVM. Call whenever done with the calculator.
        """
        if jp.isJVMStarted():
            logging.info('Shutting down JVM...')
            jp.shutdownJVM()


@click.command()
@click.option('--filename',  help = 'Numpy array dump of microscopic features of the system', required = True)
@click.option('--threshold', help = 'Number of timesteps to wait before calculation, at least as many as the dimenstions of the system')
def test(filename: str, threshold: int = SAMPLE_THRESHOLD) -> None:
    """
    Test the emergence calculator on the trajectories specified in `filename`.
    """
    calc = EmergenceCalculator(compute_macro)

    X = np.load(filename, allow_pickle=True)
    for i in range(len(X)):
        psi = calc.update_and_compute(X[i])
        if psi:
            print(f't{i}: {psi}')

    calc.exit()


if __name__ == "__main__":
    test()
