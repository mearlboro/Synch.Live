#!/usr/bin/python
import click

import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import time
import yaml

from typing import Any, List, Tuple, Optional, Union

from camera.core.detection import Detector
from camera.core.tracking import EuclideanMultiTracker
from camera.tools.config import parse

def dump_trajectories(traj: List[List[np.ndarray]], out: str, players: int) -> None:
    """
    Save trajectories to specified filename in media folder
    """
    # TODO: issues with the 11th player
    new_traj = []
    for i, state in enumerate(traj):
        if len(state) == players:
            new_traj.append(state)
        elif len(state) < players:
            print(f"{i} {state}")
    nptraj = np.array(new_traj)
    nptraj.dump(out)


def get_opencv_tracker(name: str) -> Any:
    """
    Create single OpenCV object tracker by name.

    Params
    ------
    name
        string name of openCV tracker

    Returns
    ----
    cv2.Tracker onject of that type
    """

    OPENCV_OBJECT_TRACKERS = {
        "CSRT":       cv2.TrackerCSRT_create,
        "KCF":        cv2.TrackerKCF_create,
        "BOOSTING":   cv2.TrackerBoosting_create,
        "MIL":        cv2.TrackerMIL_create,
        "TLD":        cv2.TrackerTLD_create,
        "MEDIANFLOW": cv2.TrackerMedianFlow_create,
        "MOSSE":      cv2.TrackerMOSSE_create
    }

    name = name.upper()
    if (name in OPENCV_OBJECT_TRACKERS.keys()):
        tracker = OPENCV_OBJECT_TRACKERS[name]()
    else:
        tracker = None
        print(f'Incorrect tracker name: {name}')

    return tracker


def opencv_multitracking(
        vid: cv2.VideoCapture, multiTracker: cv2.MultiTracker, det: Detector, out: str
    ) -> None:
    """
    Tracks objects in given video, drawing a video output with bounding boxes,
    and dumping coordinates of centre of mass as numpy array

    Params
    ------
    vid
        video file/stream to track
    multiTracker
        openCV multiTracker initialised with bounding boxes of the objects to
        track
    out
        filename to dump trajectories to

    Side-effects
    ------
        display the bounding boxes and object identifiers on the video
        dump coordinates as a numpy array
        exit when the key pressed is Esc
    """

    coord = list()
    traj  = list()

    while vid.isOpened():
        success, frame = vid.read()

        if not success:
            print('Failed to read frame from video')
            dump_trajectories(traj, out)
            return

        success, newBoxes = multiTracker.update(frame)

        if not success:
            print('Tracking failed')
            continue

        det.draw_annotations(frame, newBoxes)
        cmass = [ np.array([x+w/2, y+h/2]) for (x, y, w, h) in newBoxes ]
        traj.append(cmass)

        cv2.imshow('Tracking of Synch.live players', frame)
        # wait on any key to move to the next frame, and exit if it's Esc
        if cv2.waitKey(1) & 0xFF == 27:
            dump_trajectories(traj, out)
            return


def realtime_multitracking(
        vid: cv2.VideoCapture, tracker: EuclideanMultiTracker, det: Detector, out: str
    ) -> None:
    """
    Tracks objects in given video, drawing a video output with bounding boxes,
    and dumping coordinates of centre of mass as numpy array

    Params
    ------
    vid
        video file/stream to track
    tracker
        EuclideanMultiTracker object initialised with original positions of the
        objects to be tracked
    out
        filename to dump trajectories to

    Side-effects
    ------
        display the bounding boxes and object identifiers on the video
        dump coordinates as a numpy array
        exit when the key pressed is Esc
    """

    coord = list()
    traj  = list()

    players = 0

    while vid.isOpened():
        success, frame = vid.read()

        if not success:
            print('Failed to read frame from video')
            dump_trajectories(traj, out, players)
            return

        trackingBoxes = det.detect_colour(frame)
        newBoxes = tracker.update(trackingBoxes)

        if len(trackingBoxes) > players:
            players = len(trackingBoxes)
            print(f'Tracking {players} players')

        if not success:
            print('Tracking failed')
            continue

        det.draw_annotations(frame, newBoxes)
        cmass = [ np.array([x+w/2, y+h/2]) for (x, y, w, h) in newBoxes ]
        traj.append(cmass)

        cv2.imshow('Tracking of Synch.live players', frame)
        # wait on any key to move to the next frame, and exit if it's Esc
        if cv2.waitKey(1) & 0xFF == 27:
            dump_trajectories(traj, out, players)
            return



@click.command()
@click.option('--filename', help = 'Video file to track', required = True)
@click.option('--tracker',  help = 'OpenCV tracker to use', default = 'CSRT')
@click.option('--realtime', help = "If set, don't use OpenCV, but real-time tracker", is_flag = True, default = False)
@click.option('--out',      help = 'Path to directory to save array', default = '../media/trajectories/')
def track(filename: str, tracker: str, realtime: bool, out: str):
    """
    Create a VideoCapture object for a video/stream at the given path, then
    perform object detection on the first frame and proceed to object tracking
    using specified OpenCV tracker

    When done, dump to file in media/trajectories
    """

    out = out + '/' + filename.split('/')[-1].split('.')[0] + '.traj'
    print(f'Plotting trajectories to {out}')

    vid = cv2.VideoCapture(filename)
    time.sleep(0.1)

    conf_path = os.environ.get('CONFIG_PATH', default = './camera/config/default.yml')
    with open(conf_path, 'r') as fh:
        yaml_dict = yaml.safe_load(fh)
        config = parse(yaml_dict)

    det = Detector(config.detection)

    success, frame = vid.read()
    if not success:
        print('Error reading first frame')
        exit(1)

    trackingBoxes = det.detect_colour(frame)

    if realtime:
        multiTracker = EuclideanMultiTracker(config.tracking)
        for box in trackingBoxes:
            multiTracker.track(box)

        realtime_multitracking(vid, multiTracker, det, out)
    else:
        multiTracker = cv2.MultiTracker_create()
        for box in trackingBoxes:
            multiTracker.add(get_opencv_tracker(tracker), frame, box)

        opencv_multitracking(vid, multiTracker, det, out)

    vid.release()


@click.command()
@click.option('--filename', help = 'Numpy array dump of trajectories', required = True)
@click.option('--out',      help = 'Path to directory to save plot',   default = '../media/trajectories')
def plot(filename: str, out: str):
    """
    Plot the numpy array dumped by the tracker using matplotlib
    """

    X = np.load(filename, allow_pickle=True)
    (T, N, D) = X.shape

    print(f'Loaded numpy dump for {T} frames, {N} players in {D} dimensions from {filename}')

    # todo: remove out of bound points
    #if (0 < X[:, i, 0] < 1 and 0 < X[:, i, 1] < 1):
    for i in range(N-1):
        plt.plot(X[:, i, 0], X[:, i, 1], alpha = 0.5, linewidth = 1)
    plt.plot(X[:, N-1, 0], X[:, i, 1], linewidth = 2, color = 'black')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.title(f'Player trajectories (with centre of mass)')

    out = out + '/' + filename.split('/')[-1].split('.')[0] + '.png'
    print(f'Plotting trajectories to {out}')
    plt.savefig(f"{out}")


@click.command()
@click.option('--filename', help = 'Numpy array dump of trajectories', required = True)
@click.option('--out',      help = 'Path to directory to save positions, angles, velocities',
                            default = '../media/flocks')
def totxt(filename: str, out: str):
    """
    Save the numpy array dumped by the tracker in a text file for each system variable.
    E.g. x1.txt and x2.txt for the 2D coordinates, v.txt for the velocities, a.txt for
    the angle.

    Dump to media/flocks in a tab-separated file
    """
    Xt = np.load(filename, allow_pickle=True)
    (T, N, D) = Xt.shape

    dirname = out + '/' + filename.split('/')[-1].split('.')[0]
    print(f"Creating dir {dirname} to save variables as txt")
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    print(f'Loaded numpy dump for {T} frames, {N} players in {D} dimensions from {filename}')

    for t in range(T-1):
        X = Xt[t]
        with open(f"{dirname}/x1.txt", 'a') as f:
            for i in range(N):
                f.write(f"{X[i,0]}\t")
            f.write('\n')
        with open(f"{dirname}/x2.txt", 'a') as f:
            for i in range(N):
                f.write(f"{X[i,1]}\t")
            f.write('\n')

    At = []
    Vt = []
    for t1, t2 in zip(range(T-1), range(1,T)):
        A = []
        V = []
        for i in range(N):
            diff = Xt[t2][i] - Xt[t1][i]
            A.append(np.arctan2(diff[1], diff[0]))
            V.append(np.linalg.norm(diff))
        At.append(A)
        Vt.append(V)

    for t in range(T-1):
        A = At[t]
        V = Vt[t]
        with open(f"{dirname}/a.txt", 'a') as f:
            for i in range(N):
                f.write(f"{A[i]}\t")
            f.write('\n')
        with open(f"{dirname}/v.txt", 'a') as f:
            for i in range(N):
                f.write(f"{V[i]}\t")
            f.write('\n')


@click.group()
def options():
	pass

options.add_command(track)
options.add_command(totxt)
options.add_command(plot)

if __name__ == '__main__':
    options()
    cv2.destroyAllWindows()

