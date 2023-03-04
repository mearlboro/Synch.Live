from flask import Blueprint, redirect, url_for, Response, jsonify

from synch_live.camera.video.proxy import VideoProcessorClient

bp = Blueprint('tracking', __name__, url_prefix='/tracking')


@bp.route('/start')
def start_tracking():
    VideoProcessorClient().start()
    return redirect(url_for('experiment.observe'))


@bp.route('/stop')
def stop_tracking():
    VideoProcessorClient().stop()
    return redirect(url_for('main'))


@bp.route('/sync')
def sync():
    return jsonify(VideoProcessorClient().sync)


@bp.route('/feed')
def feed():
    return Response(VideoProcessorClient().generate_frame(), mimetype="multipart/x-mixed-replace; boundary=frame",
                    headers={'Cache-Control': 'no-store'})
