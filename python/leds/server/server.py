from flask import Flask, render_template, json, request, jsonify
from python.leds.ws2801_headset import WS2801Headset
import os

def create_app(server_type):
    app = Flask(__name__)
    leds = WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5)
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
        leds.all_off()
        return render_template('hat_standalone.html')

    @app.route('/ProcessNewColor/<string:newRGBValues>', methods=['POST'])
    def ProcessNewColor(newRGBValues):
        newRGBValues2 = json.loads(newRGBValues)
        newColor = newRGBValues2
        print(newColor, flush=True)

        WS2801Headset((0, 0, 100), (newColor[0], newColor[1], newColor[2]), 0.5, 1.5).crown_on()
        WS2801Headset((newColor[0], newColor[1], newColor[2]), (0,255,0), 0.5, 1.5).pilot()

        return render_template('hat_standalone.html')

    # @app.route('/get_color', methods=['POST'])
    # def get_color():
    #     color_value = request.json['color']
    #     rgb_values = tuple(int(color_value[i:i + 2], 16) for i in (1, 3, 5))
    #
    #     WS2801Headset((rgb_values[0], rgb_values[1], rgb_values[2]), (0,255,0), 0.5, 1.5).crown_on()
    #
    #     return render_template('hat_standalone.html')

    return app


if __name__ == '__main__':
    server_type = 'hats'

    host = os.environ.get('HOST', default='0.0.0.0')
    port = int(os.environ.get('PORT', default='5000'))

    app = create_app(server_type)
    app.run(debug=True)

