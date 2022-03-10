#!/usr/bin/python
from abc import ABC, abstractmethod
import cv2
import click
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import distance as dist
from scipy.optimize import linear_sum_assignment
import time
from typing import List, Tuple

from camera.core.detection import detect_colour
from camera.core.tracking import EuclideanMultiTracker

class TrajFitnessFunction(ABC):
    @abstractmethod
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

class EuclideanFitness(TrajFitnessFunction):
	"""
	Compute fitness between two sets of trajectories by computing the euclidean
	distance between them. The sets are ordered, i.e. Xi is the expected position
	tracked in Yi. The purpose of this function is to test tracking.
	"""
	@staticmethod
	def fit(X: np.ndarray, Y: np.ndarray) -> float:
		dists = [ dist.euclidean(xi, yi) for xi, yi in zip(X, Y) ]
		return np.mean(dists)

class HungarianFitness(TrajFitnessFunction):
    """
    Compute fitness between two sets of trajectories using the minimal distance
    function in the Hungarian algorithm. The sets are not necessarily ordered,
	i.e. the expected position Xi is not necessarily tracked in Yi. The purpose
	of this function is to test object detection.
    """
    @staticmethod
    def fit(X: np.ndarray, Y: np.ndarray) -> Tuple[int, float]:
        dists = dist.cdist(X, Y)
        rows, cols = linear_sum_assignment(dists)

        cost = dists[rows, cols].sum()
        miss = abs(len(rows) - len(cols))

        return cost, miss



@click.command()
@click.option('--fvid', help = 'Video file including particles to be tracked', required = True)
@click.option('--fx',   help = 'Numpy array dump of expected trajectories (precomputed on the same video file)', required = True)
@click.option('--model', help = 'Motion model to use in the tracker',
						 type =  click.Choice(['Constant', 'Kalman']))
def track(fvid: str, fx: str, model: str) -> None:
    """
    Evaluate quality of EuclideanMultitracker using model specified in `model`
    using euclidean distance
    """
    X = np.load(fx, allow_pickle = True)
    (Tx, Nx, Dx) = X.shape

    vid = object()
    try:
        vid = cv2.VideoCapture(fvid)
        time.sleep(0.1)
    except:
        print("Error reading video")
        exit(1)

    success, frame = vid.read()
    if not success:
        print("Error reading video")
        exit(1)

    tracker = EuclideanMultiTracker()
    Y = list()
    boxes = detect_colour(frame)
    Y0 = [ [ x + w / 2, y + h / 2] for (x, y, w, h) in boxes ]

    print("Making sure the expected and detected coordinates are in the same order")
    rows, cols = linear_sum_assignment(dist.cdist(X[0], Y0))
    if not all(rows == cols):
        print(f"Reordering {rows} to {cols}")
        boxes_copy = boxes
        for (r, c) in zip(rows, cols):
             boxes[r] = boxes_copy[c]

    print(f"Running real-time multitracker on video {fvid}")
    while vid.isOpened():
        success, frame = vid.read()
        if not success:
            print("Video finished")
            break

        boxes = detect_colour(frame)
        newBoxes = tracker.update(boxes)
        cmass = [ np.array([x + w / 2, y + h / 2]) for (x, y, w, h) in boxes ]
        print(len(cmass))
        Y.append(cmass)

    vid.release()

    Y = np.array(Y)
    (Ty, Ny, Dy) = Y.shape

    assert(Tx == Ty and Nx == Ny and Dx == Dy)

    cs, ms = zip(*[ EuclideanFitness.fit(x, y) for x, y in zip(X, Y) ])

    plt.title('Trajectory fitness')
    plt.plot(range(Tx), cs, label = 'Cost function of tracker', color = 'r')
    plt.plot(range(Tx), ms, label = 'Number of players missed by tracker')
    plt.legend()
    plt.show()


@click.group()
def options():
    pass

options.add_command(track)
# options.add_command(detect) TODO:

if __name__ == '__main__':
    track()

