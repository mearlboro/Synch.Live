import os
import yaml
import socket
from flask import Flask, render_template, request, redirect, url_for
from leds.tools.ws2801_headset import WS2801Headset


def create_app(server_type):
    app = Flask(__name__)
    leds = WS2801Headset((0, 0, 100), (0, 255, 0), 0.5, 1.5)
    ipAddress = socket.gethostbyname(socket.gethostname())
    lastTwoDigits = ipAddress.split(".")[-1][-2:]

    def loadHexFromYaml():
        with open('leds/server/config.yaml', 'r') as f:
            rgb = yaml.load(f, Loader=yaml.FullLoader)
            origColour = rgb['hexColor']
            frequency = rgb['frequency']
            duration = rgb['duration']
            return origColour, frequency, duration
    def webpage():
        if os.path.exists('leds/server/config.yaml'):
            origCol, freq, dur = loadHexFromYaml()
            return render_template('hat_standalone.html',
                                   lastTwoDigits=lastTwoDigits, origCol=origCol, freq=freq, dur=dur)
        else:
            return render_template('hat_standalone.html', lastTwoDigits=lastTwoDigits)

    @app.route("/")
    def main():
        return webpage()

    @app.route('/pilotButton')
    def pilotButton():
        leds.pilot()
        return webpage()

    @app.route('/rainbowButton')
    def rainbowButton():
        leds.crown_rainbow()
        return webpage()

    @app.route('/policeButton')
    def policeButton():
        leds.crown_police()
        return webpage()

    @app.route('/paparazziButton')
    def paparazziButton():
        leds.crown_paparazzi()
        return webpage()

    @app.route('/fireButton')
    def fireButton():
        leds.crown_fire()
        return webpage()

    @app.route('/partyButton')
    def partyButton():
        return webpage()

    @app.route('/exposureButton')
    def exposureButton():
        leds.crown_on()
        leds.pilot()
        return webpage()

    @app.route('/breatheButton')
    def breatheButton():
        leds.crown_breathe()
        return webpage()

    @app.route('/startButton')
    def startButton():
        if os.path.exists('leds/server/config.yaml'):
            # load RGB values from YAML file
            with open('leds/server/config.yaml', 'r') as f:
                rgb = yaml.load(f, Loader=yaml.FullLoader)
                r = rgb['r']
                g = rgb['g']
                b = rgb['b']
                origCol = rgb['hexColor']
                frequency = int(request.form['blickfrequency'])
                duration = int(request.form['effectduration'])
                # do something with the RGB values
                WS2801Headset((r, g, b), (r, g, b), 0.5, 1.5).crown_on()
            return render_template('hat_standalone.html',
                                   lastTwoDigits=lastTwoDigits, origCol=origCol, freq=frequency, dur=duration)
        else:
            return render_template('hat_standalone.html', lastTwoDigits=lastTwoDigits)

    @app.route('/stopButton')
    def stopButton():
        leds.crown_off()
        leds.all_off()
        return webpage()

    @app.route('/clearButton')
    def clearButton():
        if os.path.exists("leds/server/config.yaml"):
            os.remove("leds/server/config.yaml")
        return webpage()

    @app.route('/handle_color_picker', methods=['POST'])
    def handle_color_picker():

        color = request.form['color']
        # color is a string in the format "#RRGGBB"
        origCol = color
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        frequency = int(request.form['blickfrequency'])
        duration = int(request.form['effectduration'])

        if 'TrialConfigButton' in request.form:
            # Trial run the lights
            leds.crown_trial_config(r=r, g=g, b=b, blink_freq=frequency, effect_dur=duration)
        elif 'saveConfigButton' in request.form:
            # Save the configuration to YAML file
            with open('leds/server/config.yaml', 'w') as f:
                yaml.dump({'hexColor': origCol, 'r': r, 'g': g, 'b': b, 'frequency': frequency, 'duration': duration}, f)

        return render_template('hat_standalone.html',
                               lastTwoDigits=lastTwoDigits, origCol=origCol, freq=frequency, dur=duration)

    return app


if __name__ == '__main__':
    server_type = 'hats'

    app = create_app(server_type)
    app.run(host='0.0.0.0', port=5000, debug=True)
