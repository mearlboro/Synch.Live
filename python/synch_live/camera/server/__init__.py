import os
import threading
from multiprocessing import current_process

from flask import Flask, render_template, url_for, send_from_directory
from . import download

from synch_live.camera.video.proxy import VideoProcessorServer
from ..video.pool import VideoProcessHandle

def is_parent_process():
    return current_process().__getattribute__('_parent_pid') is None


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        ### Commented out db so we don't have multiple dbs
        #DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        VIDEO_CONFIG=os.path.join(app.instance_path, 'video_config.yml'),
        ANSIBLE_DIR=os.path.join(app.root_path, '../../../../ansible'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    @app.template_global()
    def navigation():
        return [
            dict(href=url_for('main'), caption='Home'),
            dict(href=url_for('setup.start_setup'), caption='Setup'),
            dict(href=url_for('setup_items.start_setup'), caption='Setup Items'),
            dict(href=url_for('tracking.control'), caption='Experiment'),
            dict(href=url_for('download.get_data'), caption='Data'),
        ]

    @app.template_global()
    def importmap():
        return {
            "imports": {
                "@hotwired/turbo": url_for('node_modules', filename='@hotwired/turbo/dist/turbo.es2017-esm'),
                "@hotwired/stimulus": url_for('node_modules', filename='@hotwired/stimulus/dist/stimulus'),
                "@hotwired/turbo-rails": url_for('node_modules',
                                                 filename='@hotwired/turbo-rails/app/javascript/turbo/index'),
            }
        }

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if is_parent_process() and threading.current_thread() is threading.main_thread():
        VideoProcessHandle().exec(VideoProcessorServer, app.config['VIDEO_CONFIG'])

    @app.route('/')
    def main():
        return render_template('main.html', players=[])

    app.add_url_rule(
        f"{'/node_modules'}/<path:filename>",
        endpoint="node_modules",
        view_func=lambda **kw: send_from_directory('node_modules', path=f"{kw['filename']}.js"),
    )

    from . import setup, setup_items, experiment, tracking, download, players_listener
    app.register_blueprint(setup.bp)
    app.register_blueprint(setup_items.bp)
    app.register_blueprint(experiment.bp)
    app.register_blueprint(tracking.bp)
    app.register_blueprint(download.bp)
    app.register_blueprint(players_listener.bp)

    return app

