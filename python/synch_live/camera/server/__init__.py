import os
import threading
import weakref

from flask import Flask, render_template, url_for, send_from_directory
from . import download

from synch_live.camera.video.proxy import VideoProcessorServer, video_process, VideoProcessorClient


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        VIDEO_CONFIG=os.path.join(app.instance_path, 'video_config.yml'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    @app.template_global()
    def navigation():
        tracking_toggle_label = f'{"Stop" if VideoProcessorClient().running else "Start"} tracking'
        return [
            dict(href=url_for('main'), caption='Home'),
            dict(href=url_for('setup.start_setup'), caption='Setup'),
            dict(href=url_for('tracking.control'), caption='Experiment'),
            dict(href=url_for('tracking.toggle'), caption=tracking_toggle_label),
            dict(href=url_for('calibrate.calibrate'), caption='Calibrate'),
            dict(href=url_for('experiment.observe'), caption='Observe'),
            dict(href=url_for('download.get_data'), caption='Data'),
        ]

    @app.template_global()
    def importmap():
        return {
            "imports": {
                "@hotwired/turbo": url_for('node_modules', filename='@hotwired/turbo/dist/turbo.es2017-esm.js'),
                "@hotwired/stimulus": url_for('node_modules', filename='@hotwired/stimulus/dist/stimulus.js'),
            }
        }

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if threading.current_thread() is threading.main_thread():
        video_process.submit(VideoProcessorServer, app.config['VIDEO_CONFIG']).result()

    @app.route('/')
    def main():
        players = [dict(caption=f"Player {n}", href=f"http://player{n}.local:5000") for n in range(12)]
        return render_template('main.html', players=players)

    app.add_url_rule(
        f"{'/node_modules'}/<path:filename>",
        endpoint="node_modules",
        view_func=lambda **kw: send_from_directory('node_modules', path=kw['filename']),
    )

    from . import calibration, setup, experiment, tracking, download
    app.register_blueprint(calibration.bp)
    app.register_blueprint(setup.bp)
    app.register_blueprint(experiment.bp)
    app.register_blueprint(tracking.bp)
    app.register_blueprint(download.bp)

    return app

