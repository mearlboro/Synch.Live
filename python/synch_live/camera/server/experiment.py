import time

from flask import Blueprint, render_template, request, redirect, url_for, flash
from wtforms import Form, BooleanField, IntegerField, validators

from synch_live.camera.video.proxy import VideoProcessorClient

bp = Blueprint('experiment', __name__, url_prefix='/experiment')


@bp.route('/observe', methods=['GET', 'POST'])
def observe():
    
    video_processor = VideoProcessorClient()
    
    form = TaskSettings(request.form)
    
    if request.method == "POST" and form.validate():
        
        # set task to emergence if emergence button is clicked
        if form.is_emergence.data:
            
            video_processor.task = 'emergence'
            
            # writing sigmoids to database
            video_processor.sync

        # otherwise, set task to manual with given psi
        else:
            video_processor.psi = form.manual_psi.data
        
        flash('Task updated!')
        
        return redirect(url_for('experiment.observe'))
    
    return render_template('observe.html', form=form, time=time.time(), task = video_processor.task, psi = video_processor.psi)


class TaskSettings(Form):
    manual_psi = IntegerField("Switch task to 'Manual' by entering PSI:", [validators.Optional(), validators.number_range(min=0, max=10)])
    is_emergence = BooleanField("Switch task to 'Emergence':")

