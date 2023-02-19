from flask import Flask, render_template
from python.leds.ws2801_headset import WS2801Headset
import os
import logging
import python.leds.logger

def create_app(server_type):
    app = Flask(__name__)
    app.debug = True
    # conf.conf_path = conf_path
    # logging.info(f"Creating {server_type} server with config:\n{conf}")
    @app.route("/")
    def main():
        return render_template('hat_standalone.html')

    return app

    @app.route('/pilotButton')
    def pilotButton():
        WS2801Headset.pilot()

    @app.route('/rainbowButton')
    def pilotButton():
        WS2801Headset.crown_rainbow()

    @app.route('/exposureButton')
    def pilotButton():
        return

    @app.route('/breatheButton')
    def pilotButton():
        WS2801Headset.crown_breathe()

    @app.route('/stopButton')
    def pilotButton():
        WS2801Headset.all_off()


if __name__ == '__main__':
    server_type='hats'

    host = os.environ.get('HOST', default = '0.0.0.0')
    port = int(os.environ.get('PORT', default = '8080'))
    # conf_path = os.environ.get('CONFIG_PATH', default = './camera/config/default.yml')

    logging.info(f"Starting server, listening on {host} at port {port}")

    create_app(server_type).run(
        host = host, port = port, debug = True,
        threaded = True, use_reloader = False)
