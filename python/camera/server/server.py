import sys, os
from flask import Flask, jsonify, render_template, redirect, request, url_for
from flask.wrappers import Response
import signal
import logging

# import files performing calibration and tracking
from video import VideoProcessor

awb_modes = [
    "off",
    "auto",
    "sunlight",
    "cloudy",
    "shade",
    "tungsten",
    "fluorescent",
    "incandescent",
    "flash",
    "horizon",
    "greyworld"
]

def create_app(server_type):
    app = Flask(__name__)
    app.debug = True
    app.config['RECORD_PATH'] = os.environ.get('RECORD_PATH', default='media/video')
    app.config['VIDEO_PATH'] = os.environ.get('VIDEO_PATH', default='media/video/3.avi')

    logging.info(f"Creating {server_type} server")
    if server_type == 'local':
        logging.info(f"Using preloaded video stream at {app.config['VIDEO_PATH']}")
        proc = VideoProcessor(
            use_picamera = False,
            record = False,
            annotate = True,
            video = app.config['VIDEO_PATH'],
            record_path = app.config['RECORD_PATH']
        )
    elif server_type == 'observer':
        proc = VideoProcessor(
            use_picamera = True,
            record = True,
            annotate = True,
            record_path=app.config['RECORD_PATH']
        )
    else:
        raise ValueError(f"Unsupported Server Type: {server_type}")

    def handler(signum, frame):
        res = input("Do you want to exit? Press y.")
        if res == 'y':
            proc.stop()
            exit(1)

    signal.signal(signal.SIGINT, handler)

    def is_running():
        if proc.running:
            return "Tracking is running, view at the live feed."
        else:
            return "Tracking is off. Please press Start Tracking to begin the experiment."

    @app.route("/")
    def index():
        return render_template("index.html", running_text=is_running())

    @app.route("/sync")
    def return_sync():
        return jsonify(proc.Sync)

    @app.route("/start_tracking")
    def start_tracking():
        if not proc.running:
            proc.start()
        return redirect(url_for("observe"))

    @app.route("/stop_tracking")
    def stop_tracking():
        if proc.running:
            proc.stop()
        return redirect(url_for("index"))

    @app.route("/calibrate", methods=['GET', 'POST'])
    def calibrate():
        if request.method == 'POST':
            iso = request.form['iso']
            saturation = request.form['saturation']
            awb_mode = request.form['awb_mode']
            shutter_speed = request.form['shutter_speed']
            proc.picamera.iso = int(iso)
            proc.picamera.shutter_speed = int(shutter_speed)
            proc.picamera.saturation = int(saturation)
            proc.picamera.awb_mode = awb_mode
        if proc.use_picamera:
            pi_opts = proc.picamera
        else:
            pi_opts = {}
        return render_template("calibrate.html", use_picamera=proc.use_picamera, pi_opts=pi_opts, awb_modes=awb_modes)

    @app.route("/observe", methods = ['GET', 'POST'])
    def observe():
        if request.method == "POST":
            psi = int(request.form.get("manPsi"))
            proc.set_manual_psi(psi)
            return render_template("observe.html", running_text=is_running(), psi=proc.psi)
            #return redirect(url_for('observe'))
        return render_template("observe.html", running_text=is_running(), psi=proc.psi)

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

    return app


if __name__ == '__main__':
    server_type='observer'
    if len(sys.argv) > 1:
        server_type = sys.argv[1]
    # start the flask app
    host = os.environ.get('HOST', default='0.0.0.0')
    port = int(os.environ.get('PORT', default='8888'))
    logging.info(f"Starting server, listening on {host} at port {port}")
    create_app(server_type).run(host=host, port=port, debug=True,
            threaded=True, use_reloader=False)
