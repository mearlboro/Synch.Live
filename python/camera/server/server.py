import sys, os
from flask import Flask, jsonify, render_template, redirect, request, url_for
from flask.wrappers import Response
from imutils.video import VideoStream
import signal
import logging
import yaml
from types import SimpleNamespace
from copy import deepcopy

from camera.tools.config import parse, unparse, unwrap_hsv
from camera.tools.colour import hsv_to_hex
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

def create_app(server_type, conf, conf_path, camera_stream=None):
    app = Flask(__name__)
    app.debug = True
    conf.conf_path = conf_path

    logging.info(f"Creating {server_type} server with config:\n{conf}")
    proc = VideoProcessor(conf, camera_stream)

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

    @app.route("/calibrate", methods = [ 'GET', 'POST' ])
    def calibrate():
        use_picamera = proc.config.server.CAMERA == 'pi'

        if request.method == 'GET':
            opts = unparse(proc.config)
            # color picker expects hex colours
            opts['detection']['min_colour'] = hsv_to_hex(vars(proc.config.detection.min_colour))
            opts['detection']['max_colour'] = hsv_to_hex(vars(proc.config.detection.max_colour))

            return render_template("calibrate.html", use_picamera = use_picamera,
                conf_path = proc.config.conf_path, save_file = False, opts = opts, awb_modes = awb_modes)
        else:
            proc.update_tracking_conf(request.form['max_players'])
            proc.update_detection_conf(
                request.form['min_contour'], request.form['max_contour'],
                request.form['min_colour'], request.form['max_colour'])

            if use_picamera:
                proc.update_picamera(request.form['iso'], request.form['shutter_speed'],
                    request.form['saturation'], request.form['awb_mode'])

            if 'save_file' in request.form:
                conf_path = request.form['conf_path']
                file = open(conf_path, 'w')
                conf_to_save = deepcopy(proc.config)
                conf_to_save.detection.min_colour = parse(unwrap_hsv(conf_to_save.detection.min_colour))
                conf_to_save.detection.max_colour = parse(unwrap_hsv(conf_to_save.detection.max_colour))
                delattr(conf_to_save, 'conf_path')
                yaml.dump(unparse(conf_to_save), file)

            return redirect(url_for("calibrate"))

    @app.route("/observe", methods = ['GET', 'POST'])
    def observe():
        if request.method == "POST":
            psi = int(request.form.get("manPsi"))
            use_psi = request.form.get("psi")

            if use_psi:
                proc.task = 'emergence'
            else:
                proc.set_manual_psi(psi)
            return render_template("observe.html", running_text=is_running(), psi=proc.psi, task=proc.task)
        return render_template("observe.html", running_text=is_running(), psi=proc.psi, task=proc.task)

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

    host = os.environ.get('HOST', default = '0.0.0.0')
    port = int(os.environ.get('PORT', default = '8888'))
    conf_path = os.environ.get('CONFIG_PATH', default = './camera/config/default.yml')
    print(os.path.abspath("."))

    logging.info(f"Starting server, listening on {host} at port {port}, using config at {conf_path}")

    with open(conf_path, 'r') as fh:
        yaml_dict = yaml.safe_load(fh)
        config = parse(yaml_dict)

        # NOTE: to use /dev/video* devices, you must launch in the main process
        #       so we create the camera stream here
        camera_number = config.server.CAMERA
        camera_stream = None
        if camera_number != None:
            logging.info(f"Opening Camera {camera_number}")
            camera_stream = VideoStream(int(camera_number))

        create_app(server_type, config, conf_path, camera_stream=camera_stream).run(
                host = host, port = port, debug = True,
                threaded = True, use_reloader = False)
