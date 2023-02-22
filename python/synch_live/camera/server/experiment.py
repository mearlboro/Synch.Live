from flask import Blueprint, render_template, request

from synch_live.camera.video.video import VideoProcessorProxy

bp = Blueprint('experiment', __name__, url_prefix='/experiment')


@bp.route('/observe')
def observe():
    if request.method == "POST":
        psi = int(request.form.get("manPsi"))
        use_psi = request.form.get("psi")

        if use_psi:
            VideoProcessorProxy().task = 'emergence'
        else:
            VideoProcessorProxy().set_manual_psi(psi)
    return render_template('observe.html')
