from flask import Response, Flask, render_template
from imutils.video import VideoStream
import logging
import numpy as np
from picamera import PiCamera
import threading
import time

from typing import List, Tuple, Generator

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
video_stream = VideoStream(usePiCamera=1, resolution=(640,480), framerate=12).start()
time.sleep(1)

# define video writer to save the stream
codec = cv2.VideoWriter_fourcc(*'MJPG')
date  = datetime.datetime.now().strftime('%y-%m-%d_%H%M')
video_writer    = cv2.VideoWriter(f'output_{date}.avi', codec, 12.0, (640, 480))


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



def tracking(annotate: bool = True, record: bool = True) -> None:
    """
    Tracking process, starting with initial object detection, then fetch a
    new frame and track. Annotate image and produce a streamable output
    via the global output_frame variable.

    Side-effects
    ------
        - produce a stream in output_frame
        - may acquire or release lock
        - consumes the video stream
        - logs tracked positions to log file
    """
    global video_stream, video_writer, output_frame, lock

    # read the first frame and detect objects
    with lock:
        frame = video_stream.read()
        if record:
            video_writer.write(frame)

    if frame is None:
        logging.info('Error reading first frame. Exiting.')
        exit(0)
    logging.info('Detect all object in frame.')

    bboxes = detect_colour(frame)
    if annotate:
        frame = draw_annotations(frame, bboxes)

    # acquire the lock, set the output frame, and release the lock
    with lock:
        output_frame = frame.copy()

    # loop over frames from the video stream and track
    while True:
        with lock:
            frame = video_stream.read()
            if record:
                video_writer.write(frame)

        new_bboxes = EuclideanMultiTracker(frame, bboxes)

        if (len(new_bboxes) == len(bboxes)):
            bboxes = new_bboxes

        if annotate:
            frame = draw_annotations(frame, bboxes)

        # acquire the lock, set the output frame, and release the lock
        with lock:
            output_frame = frame.copy()


def generate_frame() -> Generator[bytes, None, None]:
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
    # release the video stream and writer pointers
    video_stream.stop()
    video_writer.release()
