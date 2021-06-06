from collections import OrderedDict
import logging
import numpy as np
from scipy.spatial import distance as dist
from typing import List, Tuple

# initialise logging to file
import logger


# TODO: set at calibration time
MIN_DISTANCE = 40
LOST_FRAMES  = 50


def centre_of_mass(box: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Get x,y coordinates for the centre of mass of a box
    """
    (x, y, w, h) = box
    return np.array([x + w/2, y + h/2]).astype(int)


class EuclideanMultiTracker():
    def __init__(self,
            min_distance: int = MIN_DISTANCE, lost_frames: int = LOST_FRAMES
        ) -> None:
        """
        Given a number of bounding boxes from object detection, it tracks objects
        using Euclidean distance between their centres of mass. Objects are tracked
        with an ID in the `detected` dictionary. If an object is not found, track
        for how many frames it was lost in the `vanished` dictionary.

        Params
        ------
        min_distance
            Two objects cannot come closer together than `min_distance`. This value
            should be comfortably larger than the distance an object moves between
            two frames

        lost_frames
            If the object is not found for more than `lost_frames`, it will no longer
            be tracked.
        """
        self.next_id = 0
        self.detected = OrderedDict()
        self.vanished = OrderedDict()

        self.min_distance = min_distance
        self.lost_frames  = lost_frames


    def track(self, cmass: np.ndarray) -> None:
        """
        Assigns for a detected object an object ID, and stores it in the dicts

        Params
        -----
        cmass
            numpy array of shape (2,) containing a 2D centre of mass for the
            object to be tracked
        """
        self.detected[self.next_id] = cmass
        self.vanished[self.next_id] = 0
        self.next_id += 1


    def untrack(self, obj: int) -> None:
        """
        Drop the object with key `obj` from dictionaries, as it is no longer
        being tracked
        """
        del self.detected[obj]
        del self.vanished[obj]


    def update(
            self, bboxes: List[Tuple[int, int, int, int]]
        ) -> OrderedDict:
        """
        Update centre of mass position of each object in the tracker, depending
        on whether it was found or lost.

        Params
        ------
        bboxes
            bounding boxes returned by an object detector, list of tuples
            with form (x, y, w, h)

        Returns
        ------
        the dictionary of tracked objects
        """

        if len(bboxes) == 0:
            logging.info("Nothing detected")

            for i in self.vanished.keys():
                self.vanished[i] += 1
                if self.vanished[i] > self.lost_frames:
                    self.untrack(i)

            # don't update and return previously detected objects
            return self.detected

        new_cmass = np.array([centre_of_mass(bbox) for bbox in bboxes])

        if len(self.detected) == 0:
            logging.info(f"Registering {len(bboxes)} objects in the tracker")
            for c in new_cmass:
                self.track(c)

        else:
            logging.info(f"Updating {len(bboxes)} objects in the tracker")

            old_ids   = list(self.detected.keys())
            old_cmass = list(self.detected.values())

            # we compute euclidean distances between all pairs of new and old
            # centres of mass and then sort them
            D = dist.cdist(np.array(old_cmass), new_cmass)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            # we go through distances computed between pairs of objects and
            # assign the new position based on smallest distance
            # TODO: use Hungarian algoritm
            # https://pypi.org/project/hungarian-algorithm/
            usedRows = set()
            usedCols = set()
            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue
                i = old_ids[row]
                self.detected[i] = new_cmass[col]
                self.vanished[i] = 0

                usedRows.add(row)
                usedCols.add(col)

            # we also register for tracking the objects that were not used and check
            # if anything disappeared
            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    i = old_ids[row]
                    self.vanished[i] += 1
                    if self.vanished[i] > self.lost_frames:
                        self.untrack(i)

            else:
                for col in unusedCols:
                    self.track(new_cmass[col])

        return self.detected
