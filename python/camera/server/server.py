import sys
from flask import Flask, jsonify, render_template
from flask.wrappers import Response
import signal

# import files performing calibration and tracking
from video import VideoProcessor

def create_app(server_type):
    app = Flask(__name__)
    app.debug = True

    if server_type == 'local':
        proc = VideoProcessor(
            use_picamera = False, video = '../media/video/3.avi',
            record = False, annotate = True, record_path = '../media/video')
    elif server_type == 'observer':
        proc = VideoProcessor(use_picamera = True, record = True, annotate = True)
    else:
        raise ValueError(f"Unsupported Server Type: {server_type}")

    def handler(signum, frame):
        res = input("Do you want to exit? Press y.")
        if res == 'y':
            proc.stop()
            exit(1)

    signal.signal(signal.SIGINT, handler)


    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/psi")
    def return_psi():
        return jsonify(proc.Psi)

    @app.route("/start_tracking")
    def start_tracking():
        if proc.running:
            return "Tracker is already running."
        else:
            proc.start()
            return "Started Tracker."

    @app.route("/stop_tracking")
    def stop_tracking():
        if proc.running:
            proc.stop()
            return "Successfully stopped tracker."
        else:
            return "Tracker was not running."

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

    return app


if __name__ == '__main__':
    server_type='observer'
    if len(sys.argv) > 1:
        server_type = sys.argv[1]
    print(f"Starting {server_type} server")
    # start the flask app
    create_app(server_type).run(host='0.0.0.0', port=8888, debug=True,
            threaded=True, use_reloader=False)
