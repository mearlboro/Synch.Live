import os
import yaml
import socket
from flask import Flask, render_template, request, redirect, url_for
from leds.ws2801_headset import WS2801Headset


def create_app(server_type):
    app = Flask(__name__)
    leds = WS2801Headset((0, 0, 100), (0, 255, 0), 0.5, 1.5)
    ipAddress = socket.gethostbyname(socket.gethostname())
    lastTwoDigits = ipAddress.split(".")[-1][-2:]

    def loadHexFromYaml():
        if os.path.exists('leds/server/config.yaml'):
            with open('leds/server/config.yaml', 'r') as f:
                rgb = yaml.load(f, Loader=yaml.FullLoader)
                origColour = rgb['hexColor']
                origColour2 = rgb['hexColor2']
                frequency = rgb['frequency']
                duration = rgb['duration']
                return origColour, origColour2, frequency, duration
        else:
            return '#FFFFFF','#000000', 1, 10

    def loadOnlyRGB1FromYaml():
        if os.path.exists('leds/server/config.yaml'):
            with open('leds/server/config.yaml', 'r') as f:
                rgb = yaml.load(f, Loader=yaml.FullLoader)
                r = rgb['r']
                g = rgb['g']
                b = rgb['b']
                return r, g, b
        else:
            return 255,255,255

    def loadBothRGBFromYaml():
        if os.path.exists('leds/server/config.yaml'):
            with open('leds/server/config.yaml', 'r') as f:
                rgb = yaml.load(f, Loader=yaml.FullLoader)
                r = rgb['r']
                g = rgb['g']
                b = rgb['b']
                r2 = rgb['r2']
                g2 = rgb['g2']
                b2 = rgb['b2']
                return r, g, b, r2, g2, b2
        else:
            return 0, 0, 0, 255, 255, 255

    def webpage():
        if os.path.exists('leds/server/config.yaml'):
            hexCol, hexCol2, freq, dur = loadHexFromYaml()
            return render_template('hat_standalone.html',
                                   lastTwoDigits=lastTwoDigits, origCol=hexCol, origCol2=hexCol2, freq=freq, dur=dur)
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
        leds.crown_party()
        return webpage()

    @app.route('/fadeInButton')
    def fadeInButton():
        r, g, b = loadOnlyRGB1FromYaml()
        colour = (r, g, b)
        leds.crown_fadein_colour(col=colour)
        return webpage()

    @app.route('/fadeBetweenColoursButton')
    def fadeBetweenColoursButton():
        color1, color2, frequency, duration = loadHexFromYaml()
        r = int(color1[1:3], 16)
        g = int(color1[3:5], 16)
        b = int(color1[5:7], 16)
        r2 = int(color2[1:3], 16)
        g2 = int(color2[3:5], 16)
        b2 = int(color2[5:7], 16)
        colour1 = (r, g, b)
        colour2 = (r2, g2, b2)
        leds.crown_fade_between_colours(col1=colour1, col2=colour2, dur=duration)
        return webpage()

    @app.route('/exposureButton')
    def exposureButton():
        leds.crown_on()
        leds.pilot()
        return webpage()

    @app.route('/breatheButton')
    def breatheButton():
        r,g,b = loadOnlyRGB1FromYaml()
        colour = (r,g,b)
        leds.crown_breathe(col=colour)
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
                frequency = rgb['frequency']
                duration = rgb['duration']
                leds.crown_run_config(r=r, g=g, b=b, blink_freq=frequency, effect_dur=duration)
        else:
            leds.crown_run_config(r=43, g=67, b=220, blink_freq=1, effect_dur=5)
        return webpage()


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
        color2 = request.form['color2']
        # color is a string in the format "#RRGGBB"
        origCol = color
        origCol2 = color2
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        r2 = int(color2[1:3], 16)
        g2 = int(color2[3:5], 16)
        b2 = int(color2[5:7], 16)
        frequency = int(request.form['blickfrequency'])
        duration = int(request.form['effectduration'])

        if 'TrialConfigButton' in request.form:
            # Trial run the lights
            leds.crown_trial_config(r=r, g=g, b=b, blink_freq=frequency, effect_dur=duration)
        elif 'saveConfigButton' in request.form:
            # Save the configuration to YAML file
            with open('leds/server/config.yaml', 'w') as f:
                yaml.dump({'hexColor': origCol, 'hexColor2': origCol2, 'r': r, 'g': g, 'b': b, 'r2': r2, 'g2': g2,
                           'b2': b2, 'frequency': frequency, 'duration': duration}, f)

        return render_template('hat_standalone.html',lastTwoDigits=lastTwoDigits, origCol=origCol, origCol2=origCol2,
                               freq=frequency, dur=duration)

    return app


if __name__ == '__main__':
    server_type = 'hats'

    app = create_app(server_type)
    app.run(host='0.0.0.0', port=5000, debug=True)
