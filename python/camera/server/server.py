import sys, os
from types import SimpleNamespace
from flask import Flask, jsonify, render_template, redirect, url_for
from flask.wrappers import Response
import signal
import logging
import yaml

def parse(d):
  x = SimpleNamespace()
  _ = [setattr(x, k, parse(v)) if isinstance(v, dict) else setattr(x, k, v) for k, v in d.items() ]    
  return x

# import files performing calibration and tracking
from video import VideoProcessor

def create_app(server_type, profile):
    app = Flask(__name__)
    app.debug = True
    #app.config['RECORD_PATH'] = os.environ.get('RECORD_PATH', default='media/video')

    logging.info(f"Creating {server_type} server")
    proc = VideoProcessor(profile)
    #if server_type == 'local':
    #    logging.info(f"Using preloaded video stream at {app.config['VIDEO_PATH']}")
    #    proc = VideoProcessor(profile)
    #        use_picamera = False,
    #        record = False,
    #        annotate = True,
    #        video = app.config['VIDEO_PATH'],
    #        record_path = app.config['RECORD_PATH']
    #    )
    #elif server_type == 'observer':
    #    proc = VideoProcessor(
    #        use_picamera = True,
    #        record = True,
    #        annotate = True,
    #        record_path=app.config['RECORD_PATH']
    #    )
    #else:
    #    raise ValueError(f"Unsupported Server Type: {server_type}")

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

    @app.route("/calibrate")
    def calibrate():
        use_picamera = proc.config.CAMERA == 'pi'
        if use_picamera:
            pi_opts = vars(proc.config.camera)
        else:
            pi_opts = {}
        return render_template("calibrate.html", use_picamera=use_picamera, pi_opts=pi_opts)

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
    # start the flask app
    host = os.environ.get('HOST', default='0.0.0.0')
    port = int(os.environ.get('PORT', default='8888'))
    configPath = os.environ.get('CONFIG_PATH', default='./camera/config/default.yml')
    print(os.path.abspath("."))
    logging.info(f"Starting server, listening on {host} at port {port}, using config at {configPath}")
    with open(configPath, 'r') as fh:
        yamlDict = yaml.safe_load(fh)
        print(yamlDict)
        profile = parse(yamlDict)
        create_app(server_type, profile).run(host=host, port=port, debug=True,
                threaded=True, use_reloader=False)
