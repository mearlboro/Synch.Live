import logging
import numpy as np
from scipy.spatial import distance as dist
from scipy.optimize import linear_sum_assignment
from typing import List, Tuple

# initialise logging to file
import camera.core.logger

from camera.core.motion_model import ConstantMotionModel, KFMotionModel


# TODO: set at calibration time
MIN_DISTANCE = 10
LOST_FRAMES  = 50
NUM_PLAYERS  = 10


class EuclideanMultiTracker():
    def __init__(self,
            min_distance: int = MIN_DISTANCE, lost_frames: int = LOST_FRAMES,
            num_players : int = NUM_PLAYERS
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
        self.detected  = []
        self.momodels  = []

        self.min_distance = min_distance
        self.lost_frames  = lost_frames
        self.num_players  = num_players

        self.MoMoClass = ConstantMotionModel


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
            self, bboxes: List[Tuple[float, float, float, float]]
        ) -> List[Tuple[float, float, float, float]]:
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

        if len(self.momodels) == 0:
            # No momodels so far -- initialise one for each bbox
            logging.info("First detection, initialising motion models")
            self.momodels = [self.MoMoClass(bb) for bb in bboxes]
            self.detected = bboxes

        elif len(bboxes) == 0:
            # No bboxes detected -- update all models manually
            logging.info("Nothing detected, using all motion models")
            for i, mm in enumerate(self.momodels):
                self.detected[i] = mm.predict_bbox()
                mm.update(self.detected[i])

        else:
            # Some boxes detected -- running Hungarian algorithm
            logging.info(f"Updating {len(bboxes)} objects in the tracker")

            num_detections = len(bboxes)
            num_momodels   = len(self.momodels)
            predicted_pos = np.array([mm.predict() for mm in self.momodels])

            cmass = lambda x, y, w, h: np.array([x + w/2, y + h/2])
            new_cmass = np.array([ cmass(*bbox) for bbox in bboxes ])

            # we compute Euclidean distances between all pairs of new and old
            # centres of mass
            dists = dist.cdist(predicted_pos, new_cmass)
            assert(dists.shape == (num_momodels, num_detections))

            # use Hungarian algorithm to match an object's old and new positions
            rows, cols = linear_sum_assignment(dists)
            A = np.zeros([num_momodels, num_detections])
            A[rows, cols] = 1

            # match detected bboxes against known motion models. If a motion
            # model has no matching detection, update with its mean prediction
            for i in range(num_momodels):
                if A[i,:].sum() > 0.5:
                    idx = np.where(A[i,:] > 0.5)[0][0]
                    self.detected[i] = bboxes[idx]
                    ## TODO: Run full update detected momodels here, and partial
                    ## (masked?) update of un-detected momodels
                else:
                    self.detected[i] = self.momodels[i].predict_bbox()

            for mm, bbox in zip(self.momodels, self.detected):
                mm.update(bbox)

            if num_momodels < num_detections <= self.num_players:
                # More detections than momodels -- create new ones
                logging.info(f"Initialising extra objects in the tracker")
                for i in range(num_detections):
                    # Find detections that were not matched with previous momodels
                    if A[:,i].sum() < 0.5:
                        idx = np.where(A[:,i] < 0.5)[0][0]
                        self.momodels.append(self.MoMoClass(bboxes[idx]))


        return self.detected


