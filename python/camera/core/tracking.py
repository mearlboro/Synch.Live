from collections import OrderedDict
import logging
import numpy as np
from scipy.spatial import distance as dist
from scipy.optimize import linear_sum_assignment
from typing import List, Tuple

# initialise logging to file
import camera.core.logger


# TODO: set at calibration time
MIN_DISTANCE = 10
LOST_FRAMES  = 50


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
        self.detected  = OrderedDict()
        self.vanished  = OrderedDict()

        self.min_distance = min_distance
        self.lost_frames  = lost_frames


    def track(self, box: np.ndarray) -> None:
        """
        Assigns for a detected object an object ID, and stores it in the dicts

        Params
        -----
        cmass
            numpy array of shape (2,) containing a 2D centre of mass for the
            object to be tracked
        """
        self.detected[self.next_id] = box
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

        if len(self.detected) == 0:
            logging.info(f"Registering {len(bboxes)} objects in the tracker")
            for bbox in bboxes:
                self.track(bbox)

        else:
            logging.info(f"Updating {len(bboxes)} objects in the tracker")

            cmass = lambda x, y, w, h: np.array([x + w/2, y + h/2]).astype(int)

            old_ids   = list(self.detected.keys())
            old_cmass = np.array([ cmass(*bbox) for bbox in list(self.detected.values()) ])
            new_cmass = np.array([ cmass(*bbox) for bbox in bboxes ])

            # we compute Euclidean distances between all pairs of new and old
            # centres of mass
            dists = dist.cdist(old_cmass, new_cmass)

            # use Hungarian algorithm to match an object's old and new positions
            rows, cols = linear_sum_assignment(dists)

            not_updated = set(old_ids)
            for (old_id, new_id) in zip(rows, cols):
                    self.detected[old_id] = bboxes[new_id]
                    self.vanished[old_id] = 0
                    if old_id in not_updated:
                        not_updated.remove(old_id)
            for i in not_updated:
                self.vanished[i] += 1
                if self.vanished[i] > self.lost_frames:
                    self.untrack(i)

        return self.detected
