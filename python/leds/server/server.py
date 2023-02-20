from flask import Flask, render_template, json
from python.leds.ws2801_headset import WS2801Headset
import os

def create_app(server_type):
    app = Flask(__name__)
    @app.route("/")
    def main():
        return render_template('hat_standalone.html')

    @app.route('/pilotButton')
    def pilotButton():
        WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5).pilot()
        return render_template('hat_standalone.html')

    @app.route('/rainbowButton')
    def rainbowButton():
        WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5).crown_rainbow()
        return render_template('hat_standalone.html')

    @app.route('/exposureButton')
    def exposureButton():
        WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5).crown_on()
        WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5).pilot()
        return render_template('hat_standalone.html')

    @app.route('/breatheButton')
    def breatheButton():
        WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5).crown_breathe()
        return render_template('hat_standalone.html')

    @app.route('/stopButton')
    def stopButton():
        WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5).all_off()
        return render_template('hat_standalone.html')

    @app.route('/ProcessNewColor/<string:newRGBValues>', methods=['POST'])
    def ProcessNewColor(newRGBValues):
        newRGBValues2 = json.loads(newRGBValues)
        newColor = newRGBValues2
        print(newColor, flush=True)

        return render_template('hat_standalone.html')

    return app


if __name__ == '__main__':
    server_type = 'hats'

    host = os.environ.get('HOST', default='0.0.0.0')
    port = int(os.environ.get('PORT', default='5000'))

    app = create_app(server_type)
    app.run(debug=True)

