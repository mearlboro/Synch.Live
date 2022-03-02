from collections import OrderedDict
import logging
import numpy as np
from scipy.spatial import distance as dist
from scipy.optimize import linear_sum_assignment
from typing import List, Tuple
from pykalman import KalmanFilter

# initialise logging to file
import camera.core.logger

# import matplotlib.pyplot as plt


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
        self.detected  = OrderedDict()
        self.vanished  = OrderedDict()
        self.momodels  = []

        self.min_distance = min_distance
        self.lost_frames  = lost_frames
        self.num_players  = num_players


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

        # import ipdb; ipdb.set_trace()

        if len(self.momodels) == 0:
            logging.info("First detection, initialising motion models")
            self.momodels = [MotionModel(bb) for bb in bboxes]
            self.detected = dict(zip(range(self.num_players), bboxes))

        # if len(bboxes) == 0:
        #     logging.info("Nothing detected")

        #     for i in self.vanished.keys():
        #         self.vanished[i] += 1
        #         if self.vanished[i] > self.lost_frames:
        #             self.untrack(i)

        #     # don't update and return previously detected objects
        #     return self.detected

        # if len(self.detected) == 0:
        #     logging.info(f"Registering {len(bboxes)} objects in the tracker")
        #     for bbox in bboxes:
        #         self.track(bbox)

        else:
            logging.info(f"Updating {len(bboxes)} objects in the tracker")



            # current_pos = np.vstack([mm.trajectory[-1] for mm in self.momodels])
            # predicted_pos = np.vstack([mm.predict_mean() for mm in self.momodels])
            # print('=================')
            # print(current_pos)
            # print(predicted_pos)
            # print('=================')
            # plt.figure(figsize=(10,10))
            # plt.scatter(current_pos[:,0], current_pos[:,1], 'g')
            # plt.scatter(predicted_pos[:,0], predicted_pos[:,1], 'r')
            # plt.show()




            ## TODO: From here until the Hungarian algorithm assignment, this
            ## could be refactored into MotionModel, so that in the future it
            ## may be generalised as maximum likelihood assignment instead of
            ## minimum distance
            num_detections = len(bboxes)
            predicted_pos = np.array([mm.predict_mean() for mm in self.momodels])

            cmass = lambda x, y, w, h: np.array([x + w/2, y + h/2]).astype(int)
            new_cmass = np.array([ cmass(*bbox) for bbox in bboxes ])

            # we compute Euclidean distances between all pairs of new and old
            # centres of mass
            dists = dist.cdist(predicted_pos, new_cmass)
            assert(dists.shape == (self.num_players, num_detections))

            # use Hungarian algorithm to match an object's old and new positions
            rows, cols = linear_sum_assignment(dists)
            A = np.zeros([self.num_players, num_detections])
            A[rows, cols] = 1

            # match detected bboxes against known motion models. If a motion
            # model has no matching detection, update with its mean prediction
            for i in range(self.num_players):
                if A[i,:].sum() > 0.5:
                    idx = np.where(A[i,:] > 0.5)[0][0]
                    self.detected[i] = bboxes[idx]
                    ## TODO: Run full update detected momodels here, and partial
                    ## (masked?) update of un-detected momodels
                else:
                    self.detected[i] = self.momodels[i].predict_bbox()

            for mm, bbox in zip(self.momodels, self.detected.values()):
                mm.update(bbox)


            """
            cmass = lambda x, y, w, h: np.array([x + w/2, y + h/2]).astype(int)

            old_ids   = list(self.detected.keys())
            old_cmass = np.array([ cmass(*bbox) for bbox in list(self.detected.values()) ])
            new_cmass = np.array([ cmass(*bbox) for bbox in bboxes ])

            # we compute Euclidean distances between all pairs of new and old
            # centres of mass
            dists = dist.cdist(old_cmass, new_cmass)

            # use Hungarian algorithm to match an object's old and new positions
            rows, cols = linear_sum_assignment(dists)


            ###########
            cost = dists[rows, cols].sum()
            if len(rows) != 10 or len(rows) != 10 or cost > 100:
                import ipdb; ipdb.set_trace()
            ###########

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
            """

        return self.detected


## TODO: Refactor this class into an abstract one, and then make children with
## specific time series models -- i.e. Kalman, max-likelihood Kalman, constant
## (the one in the previous implementation), fixed velocity, etc

## TODO: Update docstrings
class MotionModel():
    """
    """
    def cmass(self, x, y, w, h):
        """
        Params
        ------
        bboxes
            bounding boxes returned by an object detector, list of tuples
            with form (x, y, w, h)

        Returns
        ------
        the dictionary of tracked objects
        """
        return np.array([x + w/2, y + h/2]).astype(int)


    def __init__(self, bbox):
        """
        Params
        ------
        bboxes
            bounding boxes returned by an object detector, list of tuples
            with form (x, y, w, h)

        Returns
        ------
        the dictionary of tracked objects
        """
        self.trajectory = []

        # These parameters are for position+velocity Kalman filter
        A = [[1,0,1,0], [0,1,0,1], [0,0,1,0], [0,0,0,1]]
        C = np.eye(4)
        self.state_mean = np.array([0,0,0,0])
        self.state_cov  = np.eye(4)

        # These parameters are for position only Kalman filter
        # A = [[1., 0.], [0., 1.]]
        # C = [[1., 0.], [0., 1.]]
        # self.state_mean = [0,0]
        # self.state_cov  = [[1,0], [0,1]]

        self.kf = KalmanFilter(transition_matrices=A, observation_matrices=C,
                observation_offsets=np.array([0,0,0,0]))

        self.update(bbox)


    def update(self, bbox):
        """
        Params
        ------
        bboxes
            bounding boxes returned by an object detector, list of tuples
            with form (x, y, w, h)

        Returns
        ------
        the dictionary of tracked objects
        """
        p = self.cmass(*bbox)
        if len(self.trajectory) == 0:
            v = np.array([0,0])
        else:
            v = p - self.trajectory[-1]

        self.trajectory.append(p)
        obs = np.hstack([p, v])
        self.state_mean, self.state_cov = self.kf.filter_update(self.state_mean, self.state_cov, obs)

        self.h = bbox[2]
        self.w = bbox[3]


    def predict_mean(self):
        """
        Params
        ------
        bboxes
            bounding boxes returned by an object detector, list of tuples
            with form (x, y, w, h)

        Returns
        ------
        the dictionary of tracked objects
        """
        m, s = self.kf.filter_update(self.state_mean, self.state_cov)
        # if self.kf.observation_offsets is None:
        #     self.kf.observation_offsets = np.array([0., 0., 0., 0.])
        obs = np.dot(self.kf.observation_matrices, m) + self.kf.observation_offsets
        # NOTE: If the position-only filter is used, the next line should be only 'return obs'
        return obs[:2]


    def predict_bbox(self):
        """
        Params
        ------
        bboxes
            bounding boxes returned by an object detector, list of tuples
            with form (x, y, w, h)

        Returns
        ------
        the dictionary of tracked objects
        """
        m = self.predict_mean()
        return (m[0] - self.w/2, m[1] - self.h/2, self.w, self.h)

