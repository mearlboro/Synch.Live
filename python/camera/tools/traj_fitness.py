#!/usr/bin/python
import click

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import distance as dist
from scipy.optimize import linear_sum_assignment

from typing import List, Tuple

class TrajFitnessFunction:
    @classmethod
    def fit(X: np.ndarray, Y: np.ndarray) -> float:
        """
        Calculate how well the approximate trajectories in Y fit with the real
        trajectories in X.

        Params
        ------
        X
            the true trajectories
        Y
            the approximate trajectories produced by a tracker
        """
        pass


class HungarianFitness(TrajFitnessFunction):
    """
    Compute fitness between two sets of trajectories using the minimal distance
    function in the Hungarian algorithm
    """
    @staticmethod
    def fit(X: np.ndarray, Y: np.ndarray) -> Tuple[int, float]:
        dists = dist.cdist(X, Y)
        rows, cols = linear_sum_assignment(dists)

        cost = dists[rows, cols].sum()
        miss = abs(len(rows) - len(cols))

        return cost, miss


@click.command()
@click.option('--fx', help = 'Numpy array dump of expected trajectories', required = True)
@click.option('--fy', help = 'Numpy array dump of approximate trajectories', required = True)
@click.option('--fitness', help = 'Fitness function to use when verifying the tracker works')
def track(fx: str, fy: str, fitness: str) -> None:

    X = np.load(fx, allow_pickle = True)
    (Tx, Nx, Dx) = X.shape
    Y = np.load(fy, allow_pickle = True)
    (Ty, Ny, Dy) = Y.shape

    assert(Tx == Ty and Nx == Ny and Dx == Dy)

    cs, ms = zip(*[ HungarianFitness.fit(x, y) for x, y in zip(X, Y) ])

    plt.title('Trajectory fitness using the Hungarian algorithm')
    plt.plot(range(Tx), cs, label = 'Cost function of tracker', color = 'r')
    plt.plot(range(Tx), ms, label = 'Number of players missed by tracker')
    plt.legend()
    plt.show()


@click.group()
def options():
    pass

options.add_command(track)

if __name__ == '__main__':
    options()

