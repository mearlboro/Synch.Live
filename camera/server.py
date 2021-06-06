from flask import Response, Flask, render_template
import threading
import time
from typing import List, Tuple

# import files performing calibration and tracking
from camerahelper import generate_frame, tracking


app = Flask(__name__)
app.debug    = True
app.threaded = True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/calibrate")
def calibrate():
    # start a thread that will perform motion detection
    t = threading.Thread(target=tracking)
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
    return Response(generate_frame(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':

    # start the flask app
    app.run(host='192.168.100.100', port=8888, debug=True,
            threaded=True, use_reloader=False)
