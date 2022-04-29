import sys, os
from types import SimpleNamespace
from flask import Flask, jsonify, render_template, redirect, url_for, request
from flask.wrappers import Response
import signal
import logging
import yaml

from camera.tools.config import parse, unparse
from camera.tools.colour import hsv_to_hex
from video import VideoProcessor


def create_app(server_type, conf, conf_path):
    app = Flask(__name__)
    app.debug = True

    logging.info(f"Creating {server_type} server")
    proc = VideoProcessor(conf)

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

    @app.route("/psi")
    def return_psi():
        return jsonify(proc.Psi)

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
            # for calibration no task should be run
            opts['game']['task'] = ''
            # color picker expects hex colours
            opts['detection']['min_colour'] = hsv_to_hex(vars(proc.config.detection.min_colour))
            opts['detection']['max_colour'] = hsv_to_hex(vars(proc.config.detection.max_colour))

            return render_template("calibrate.html", use_picamera = use_picamera,
                conf_path = conf_path, save_file = False, opts = opts)
        else:
            proc.update_tracking_conf(request.form['max_players'])
            proc.update_detection_conf(
                request.form['min_contour'], request.form['max_contour'],
                request.form['min_colour'], request.form['max_colour'])

            if use_picamera:
                proc.update_picamera(request.form['iso'], request.form['shutter_speed'],
                    request_form['saturation'], request.form['awb_mode'])

            return redirect(url_for("calibrate"))

    @app.route("/observe")
    def observe():
        return render_template("observe.html", running_text=is_running())

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

        create_app(server_type, config, conf_path).run(
                host = host, port = port, debug = True,
                threaded = True, use_reloader = False)
