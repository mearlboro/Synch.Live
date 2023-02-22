from flask import Blueprint, redirect, url_for, Response, jsonify

from synch_live.camera.video.video import VideoProcessorProxy

bp = Blueprint('tracking', __name__, url_prefix='/tracking')


@bp.route('/start')
def start_tracking():
    VideoProcessorProxy().start()
    return redirect(url_for('experiment.observe'))


@bp.route('/stop')
def stop_tracking():
    VideoProcessorProxy().stop()
    return redirect(url_for('main'))


@bp.route('/sync')
def sync():
    return jsonify(VideoProcessorProxy().sync)


@bp.route('/feed')
def feed():
    return Response(VideoProcessorProxy().generate_frame(), mimetype="multipart/x-mixed-replace; boundary=frame")
