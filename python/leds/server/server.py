import os
from flask import Flask, render_template, request, redirect, url_for
from leds.tools.ws2801_headset import WS2801Headset

def create_app(server_type):
    app = Flask(__name__)
    leds = WS2801Headset((0, 0, 100), (0, 255, 0), 0.5, 1.5)

    @app.route("/")
    def main():
        return render_template('hat_standalone.html')


    @app.route('/pilotButton')
    def pilotButton():
        leds.pilot()
        return render_template('hat_standalone.html')

    @app.route('/rainbowButton')
    def rainbowButton():
        leds.crown_rainbow()
        return render_template('hat_standalone.html')

    @app.route('/policeButton')
    def policeButton():
        leds.crown_police()
        return render_template('hat_standalone.html')

    @app.route('/fireButton')
    def fireButton():
        leds.crown_fire()
        return render_template('hat_standalone.html')

    @app.route('/exposureButton')
    def exposureButton():
        leds.crown_on()
        leds.pilot()
        return render_template('hat_standalone.html')

    @app.route('/breatheButton')
    def breatheButton():
        leds.crown_breathe()
        return render_template('hat_standalone.html')

    @app.route('/stopButton')
    def stopButton():
        leds.crown_off()
        leds.all_off()
        return render_template('hat_standalone.html')

    @app.route('/handle_color_picker', methods=['POST'])
    def handle_color_picker():
        color = request.form['color']
        # color is a string in the format "#RRGGBB"
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        # do something with the RGB values
        WS2801Headset((r, g, b), (r, g, b), 0.5, 1.5).crown_on()
        # return "Color submitted: ({}, {}, {})".format(r, g, b)
        return render_template('hat_standalone.html')

    return app


if __name__ == '__main__':
    server_type='hats'

    app = create_app(server_type)
    app.run(host='0.0.0.0', port=5000, debug=True)

