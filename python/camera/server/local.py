import click
from flask import Response, Flask, jsonify, render_template
import threading
import time
from typing import List, Tuple

# import files performing calibration and tracking
from video import VideoProcessor


app = Flask(__name__)
app.debug    = True
app.threaded = True

proc = VideoProcessor(
    use_picamera = False, video = '../media/video/3.avi',
    record = False, annotate = True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/psi")
def return_psi():
    return jsonify(proc.Psi)

@app.route("/calibrate")
def calibrate():
    # start a thread that will perform motion detection
    t = threading.Thread(target=proc.tracking)
    t.daemon = True
    t.start()

    return render_template("calibrate.html")

@app.route("/observe")
def observe():
    return render_template("observe.html")

@app.route("/video_feed")
def video_feed():
    """
    Direct generated frame to webserver

    Returns
    ------
        HTTP response of corresponding type containing the generated stream
    """
    return Response(proc.generate_frame(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':

    # start the flask app
    app.run(host='0.0.0.0', port=8888, debug=True,
            threaded=True, use_reloader=False)
