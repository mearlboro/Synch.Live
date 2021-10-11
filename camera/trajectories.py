#!/usr/bin/python
import click

import cv2
import matplotlib.pyplot as plt
import numpy as np
import sys
import time

from typing import Any, List, Tuple, Optional, Union

from detection import detect_colour, draw_annotations
from tracking import EuclideanMultiTracker


def dump_trajectories(traj: List[List[np.ndarray]], out: str) -> None:
    """
    Save trajectories to specified filename in media folder
    """
    nptraj = np.array(traj)
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
        vid: cv2.VideoCapture, multiTracker: cv2.MultiTracker, out: str
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

        draw_annotations(frame, newBoxes)
        cmass = [ np.array([x+w/2, y+h/2]) for (x, y, w, h) in newBoxes ]
        traj.append(cmass)

        cv2.imshow('Tracking of Synch.live players', frame)
        # wait on any key to move to the next frame, and exit if it's Esc
        if cv2.waitKey(1) & 0xFF == 27:
            dump_trajectories(traj, out)
            return


def realtime_multitracking(
        vid: cv2.VideoCapture, tracker: EuclideanMultiTracker, out: str
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

    while vid.isOpened():
        success, frame = vid.read()

        if not success:
            print('Failed to read frame from video')
            dump_trajectories(traj, out)
            return

        trackingBoxes = detect_colour(frame)
        newBoxes = tracker.update(trackingBoxes)

        print(newBoxes)

        if not success:
            print('Tracking failed')
            continue

        draw_annotations(frame, list(newBoxes.values()))
        cmass = [ np.array([x+w/2, y+h/2]) for (x, y, w, h) in newBoxes.values() ]
        traj.append(cmass)

        cv2.imshow('Tracking of Synch.live players', frame)
        # wait on any key to move to the next frame, and exit if it's Esc
        if cv2.waitKey(1) & 0xFF == 27:
            dump_trajectories(traj, out)
            return



@click.command()
@click.option('--filename', help = 'Video file to track', required = True)
@click.option('--tracker',  help = 'OpenCV tracker to use', default = 'CSRT')
@click.option('--realtime', help = "If set, don't use OpenCV, but real-time tracker", default = False)
@click.option('--out',      help = 'Filename of numpy array dumped', required = True)
def track(filename: str, tracker: str, realtime: bool, out: str):
    """
    Create a VideoCapture object for a video/stream at the given path, then
    perform object detection on the first frame and proceed to object tracking
    using specified OpenCV tracker

    When done, dump to file in media/trajectories
    """

    vid = cv2.VideoCapture(filename)
    time.sleep(0.1)

    success, frame = vid.read()
    if not success:
        print('Error reading first frame')
        exit(1)

    trackingBoxes = detect_colour(frame)

    if realtime:
        multiTracker = EuclideanMultiTracker()
        for box in trackingBoxes:
            multiTracker.track(box)

        realtime_multitracking(vid, multiTracker, out)
    else:
        multiTracker = cv2.MultiTracker_create()
        for box in trackingBoxes:
            multiTracker.add(get_opencv_tracker(tracker), frame, box)

        opencv_multitracking(vid, multiTracker, out)

    vid.release()


@click.command()
@click.option('--filename', help = 'Numpy array dump of trajectories', required = True)
@click.option('--out',      help = 'Path to save plot', required = True)
def plot(filename: str, out: str):
    """
    Plot the numpy array dumped by the tracker using matplotlib
    """

    X = np.load(filename, allow_pickle=True)
    (T, N, D) = X.shape

    print(f'Loaded numpy dump for {T} frames, {N} players in {D} dimensions')

    for i in range(N):
        plt.plot(X[:, i, 0], X[:, i, 1])
    plt.title(f'Synch live player trajectories for video {filename}')
    plt.savefig(out)


@click.group()
def options():
	pass

options.add_command(track)
options.add_command(plot)

if __name__ == '__main__':
    options()
    cv2.destroyAllWindows()

