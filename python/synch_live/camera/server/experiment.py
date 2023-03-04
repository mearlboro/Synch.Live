from flask import Blueprint, render_template, request

from synch_live.camera.video.proxy import VideoProcessorClient

bp = Blueprint('experiment', __name__, url_prefix='/experiment')


@bp.route('/observe')
def observe():
    if request.method == "POST":
        psi = int(request.form.get("manPsi"))
        use_psi = request.form.get("psi")

        if use_psi:
            VideoProcessorClient().task = 'emergence'
        else:
            VideoProcessorClient().psi = psi
    return render_template('observe.html')
