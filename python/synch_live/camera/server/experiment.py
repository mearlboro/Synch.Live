import time

from flask import Blueprint, render_template, request, redirect, url_for, flash
from wtforms import Form, BooleanField, IntegerRangeField, validators

from synch_live.camera.video.proxy import VideoProcessorClient

bp = Blueprint('experiment', __name__, url_prefix='/experiment')


@bp.route('/observe', methods=['GET', 'POST'])
def observe():
    video_processor = VideoProcessorClient()
    form = ManualSettings(request.form)
    if request.method == "POST" and form.validate():
        if form.psi.data:
            video_processor.task = 'emergence'
            # writing sigmoids to database
            video_processor.sync
        else:
            video_processor.psi = form.manual_psi.data
        flash('PSI updated!')
        return redirect(url_for('experiment.observe'))
    return render_template('observe.html', form=form, time=time.time())


class ManualSettings(Form):
    psi = BooleanField('Use PSI')
    manual_psi = IntegerRangeField('Manual PSI', [validators.number_range(min=0, max=10)])
