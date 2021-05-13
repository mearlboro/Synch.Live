from flask import Response, Flask, render_template
from imutils.video import VideoStream
import logging
import numpy as np
from picamera import PiCamera
import threading
import time

from typing import Any, List, Tuple, Optional, Union

# initialise logging to file
import logger

# import tracking code
from tracking import *

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)
# initialize the video stream and allow the sensor to warm up
vs = VideoStream(usePiCamera=1, resolution=(640,480), framerate=12).start()
time.sleep(1)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    """
    Direct generated frame to webserver

    Returns
    ------
        HTTP response of corresponding type containing the generated stream
    """
    return Response(generate_frame(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")


def tracking():
    """
    Tracking process, starting with initial object detection, then fetch a
    new frame and track. Annotate image and produce a streamable output
    via the global outputFrame variable.

    Side-effects
    ------
        - produce a stream in outputFrame
        - may acquire or release lock
        - consumes the video stream
        - updates the players dict every frame
        - logs tracked positions to log file
    """
    global vs, outputFrame, lock

    # initialize the motion detector
    multiTracker = cv2.MultiTracker_create()
    trackingBoxes = []

    # read the first frame and detect objects
    frame = vs.read()
    if frame is None:
        logging.info('Error reading first frame. Exiting.')
        exit(0)
    logging.info('Detect all object in frame.')
    boxes = detectObjectsInFrame(frame)
    frame_annot = drawAnnotations(frame, boxes)

    # acquire the lock, set the output frame, and release the lock
    with lock:
        outputFrame = frame_annot.copy()

    # initialise multitracker on detected contours
    #for box in boxes:
    #    multiTracker.add(createTrackerByName('CSRT'), frame, box)

    # loop over frames from the video stream and track
    while True:
        frame = vs.read()
        #_, newBoxes = multiTracker.update(frame)
        newBoxes = detectObjectsInFrame(frame)
        frame_annot = drawAnnotations(frame, newBoxes)

        # acquire the lock, set the output frame, and release the lock
        with lock:
            outputFrame = frame_annot.copy()


def generate_frame():
    # grab global references to the output frame and lock variables
    global outputFrame, lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
            bytearray(encodedImage) + b'\r\n')


if __name__ == '__main__':

    # start a thread that will perform motion detection
    t = threading.Thread(target=tracking)
    t.daemon = True
    t.start()
    # start the flask app
    app.run(host='192.168.100.100', port=8888, debug=True,
            threaded=True, use_reloader=False)
    # release the video stream pointer
    vs.stop()
