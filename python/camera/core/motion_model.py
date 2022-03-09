from abc import ABC, abstractmethod
import numpy as np
from pykalman import KalmanFilter

class MotionModel(ABC):
    """
    Abstract class for models of player motion, that predict the next position
    of a given player given its trajectory. Child classes must implement
    `update` and `predict` methods.
    """

    def cmass(self, x, y, w, h):
        """
        Computes the center of mass of a rectangular bounding box.

        Params
        ------
        x, y, w, h : float
            parameters of an image bounding box (x position, y position, width,
            height)

        Returns
        ------
        the coordinates of the center of mass
        """
        return np.array([x + w/2, y + h/2])


    @abstractmethod
    def update(self, bbox):
        """
        Updates the state of the motion model to reflect the latest measurement
        of the player's position.

        Params
        ------
        bbox
            bounding box returned by an object detector, tuple (x, y, w, h)
        """
        pass


    @abstractmethod
    def predict(self):
        """
        Return the predicted position of the player in the next frame, as
        estimated by the motion model.

        Returns
        ------
        iterable with estimated x,y position of the player
        """
        pass


    def predict_bbox(self):
        """
        Return the predicted bounding box of the player in the next frame, as
        estimated by the motion model and assuming a constant bounding box
        size.

        Returns
        ------
        estimated bounding box of the player, with the form (x, y, w, h)
        """
        m = self.predict()
        return (m[0] - self.w/2, m[1] - self.h/2, self.w, self.h)


class ConstantMotionModel(MotionModel):
    """
    """
    def __init__(self, bbox):
        self.update(bbox)

    def update(self, bbox):
        self.pos = self.cmass(*bbox)
        self.h = bbox[3]
        self.w = bbox[2]

    def predict(self):
        return self.pos


class KFMotionModel(MotionModel):
    """
    """
    def __init__(self, bbox):
        super().__init__()
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


    def predict(self):
        m, s = self.kf.filter_update(self.state_mean, self.state_cov)
        # if self.kf.observation_offsets is None:
        #     self.kf.observation_offsets = np.array([0., 0., 0., 0.])
        obs = np.dot(self.kf.observation_matrices, m) + self.kf.observation_offsets
        # NOTE: If the position-only filter is used, the next line should be only 'return obs'
        return obs[:2]


