from flask import Blueprint, render_template, request
from wtforms import Form, BooleanField, IntegerRangeField
from wtforms.widgets import html_params

from synch_live.camera.video.proxy import VideoProcessorClient

bp = Blueprint('experiment', __name__, url_prefix='/experiment')


@bp.route('/observe', methods=['GET','POST'])
def observe():

    form = ManualSettings(request.form)
    form.manPsi(min=0, max=10)

    if request.method == "POST":
        psi = int(request.form.get("manPsi"))
        
        if request.form.get("psi"):
            use_psi = 1
        else:
            use_psi = 0

        if use_psi:
            VideoProcessorClient().task = 'emergence'
            # writing sigmoids to database
            VideoProcessorClient().sync

        else:
            VideoProcessorClient().psi = psi
    return render_template('observe.html', form=form)

class ManualSettings(Form):
    psi = BooleanField('Psi')
    manPsi = IntegerRangeField('manPsi')

