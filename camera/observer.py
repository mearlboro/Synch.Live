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
output_frame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)
# initialize the video stream and allow the sensor to warm up
stream = VideoStream(usePiCamera=1, resolution=(640,480), framerate=12).start()
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
    via the global output_frame variable.

    Side-effects
    ------
        - may acquire or release lock
        - consumes the video stream
        - produce a video stream and send it to webserver
        - logs tracked positions to log file
    """
    global stream, output_frame, lock

    # read the first frame and detect objects
    frame = stream.read()

    if frame is None:
        logging.info('Error reading first frame. Exiting.')
        exit(0)
    logging.info('Detect all object in frame.')

    bboxes = detect_colour(frame)
    frame_annot = draw_annotations(frame, bboxes)

    # acquire the lock, set the output frame, and release the lock
    with lock:
        output_frame = frame_annot.copy()

    # loop over frames from the video stream and track
    while True:
        frame = stream.read()
        new_bboxes = EuclideanMultiTracker(frame, bboxes)

        if (len(new_bboxes) == len(bboxes)):
            bboxes = new_bboxes

        frame_annot = draw_annotations(frame, bboxes)

        # acquire the lock, set the output frame, and release the lock
        with lock:
            output_frame = frame_annot.copy()


def generate_frame():
    # grab global references to the output frame and lock variables
    global output_frame, lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if output_frame is None:
                continue
            # encode the frame in JPEG format
            (flag, encoded_frame) = cv2.imencode(".jpg", output_frame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
            bytearray(encoded_frame) + b'\r\n')


if __name__ == '__main__':

    # start a thread that will perform motion detection
    t = threading.Thread(target=tracking)
    t.daemon = True
    t.start()
    # start the flask app
    app.run(host='192.168.100.100', port=8888, debug=True,
            threaded=True, use_reloader=False)
    # release the video stream pointer
    stream.stop()
