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

# initialise logging to file
import camera.core.logger

INFODYNAMICS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'infodynamics.jar')
SAMPLE_THRESHOLD = 10

def javify(Xi):
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
    """
    if len(Xi.shape) == 1:
        D = Xi.shape[0]
        Xi = Xi[np.newaxis, :]
        jXi = jp.JArray(jp.JDouble, D)(Xi.tolist())
    else:
        D = Xi.shape[1]
        jXi = jp.JArray(jp.JDouble, D)(Xi.tolist())

    return jXi


def compute_macro(X):
    """
    Computes a supervenient macroscopic feature.

    Parameters
    ----------
    X : iter of np.ndarray
        Each element of X contains a 1D np.ndarray representing one 'micro'
        part of the system.

    Returns
    -------
    V : np.ndarray
        Macroscopic feature of interest of D-dimensions of shape (1,D)
    """
    V = np.mean(X, axis = 0)

    return V[np.newaxis, :]


class EmergenceCalculator():
    def __init__(self,
            macro_fun, #: Callable[[np.ndarray], np.ndarray],
            use_correction=True
        ) -> None:
        """
        Construct the emergence calculator by setting member variables and
        checking the JVM is started. The JIDT calculators will be initialised
        later, when the first batch of data is provided.

        Parameters
        ----------
        use_correction : bool
            Whether to use the 1st-order lattice correction for emergence
            calculation.
        """

        self.past_X = None
        self.past_V = None

        self.is_initialised = False
        self.sample_counter = 0

        self.use_correction = use_correction

        self.compute_macro = macro_fun

        if not jp.isJVMStarted():
            logging.info('Starting JVM...')
            jp.startJVM(jp.getDefaultJVMPath(), '-ea', '-Djava.class.path=%s'%INFODYNAMICS_PATH)
            logging.info('JVM started using jpype1')

        logging.info('Successfully initialised EmergenceCalculator')


    def initialise_calculators(self, X, V):
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


    def update_calculators(self, V):
        """
        """
        jV = javify(V)
        self.vmiCalc.addObservations(javify(self.past_V), jV)

        for Xip,calc in zip(self.past_X, self.xmiCalcs):
            calc.addObservations(javify(Xip), jV)


    def compute_psi(self, V):
        """
        """
        self.vmiCalc.finaliseAddObservations()
        jV = javify(V)

        psi = self.vmiCalc.computeLocalUsingPreviousObservations(
                javify(self.past_V), jV)[0]
        for Xip,calc in zip(self.past_X, self.xmiCalcs):
            calc.finaliseAddObservations()
            psi -= calc.computeLocalUsingPreviousObservations(javify(Xip), jV)[0]

        if self.use_correction:
            marginal_mi = [ calc.computeAverageLocalOfObservations()
                            for calc in self.xmiCalcs ]
            psi += (self.N - 1) * np.min(marginal_mi)

        return psi


    def update_and_compute(self, X):
        """
        """
        V = self.compute_macro(X)

        psi = 0.
        if not self.is_initialised:
            self.initialise_calculators(X, V)

        else:
            self.update_calculators(V)
            if self.sample_counter > SAMPLE_THRESHOLD:
                psi = self.compute_psi(V)

        self.past_X = X
        self.past_V = V
        self.sample_counter += 1

        logging.info(f'Psi: {psi}')

        return psi


@click.command()
@click.option('--filename',  help = 'Numpy array dump of trajectories', required = True)
@click.option('--threshold', help = 'Number of timesteps to wait before calculation')
def test(filename, threshold = SAMPLE_THRESHOLD):
    """
    Test the emergence calculator on the trajectories specified in `filename`.

    Params
    ------
    filename
        path to a numpy dump of the trajectories (microscopic) features of the system
    threshold
        number of timesteps to wait before calculation, at least as many as the
        dimension of the system
    """
    calc = EmergenceCalculator(compute_macro)

    X = np.load(filename, allow_pickle=True)
    for i in range(len(X)):
        psi = calc.update_and_compute(X[i])
        if psi:
            print(f't{i}: {psi}')


if __name__ == "__main__":
    test()
