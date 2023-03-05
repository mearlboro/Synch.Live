from flask import Blueprint, redirect, url_for, Response, jsonify, render_template, request
from wtforms import Form, StringField, BooleanField

from synch_live.camera.video.proxy import VideoProcessorClient
from synch_live.camera.db import write_in_experiment_parameters

bp = Blueprint('tracking', __name__, url_prefix='/tracking')

@bp.route('/control', methods=['GET','POST'])
def control():

    form = ExperimentInfoForm(request.form)
    
    if request.method == 'POST' and form.validate():
        experiment_id = form.experiment_id.data
        experiment_location = form.experiment_location.data
        
        if form.experiment_test.data:
            experiment_is_test = 'YES'
        else:
            experiment_is_test = 'NO'
        # writing date, start time, experiment id, location to database
        write_in_experiment_parameters(experiment_id, experiment_location, experiment_is_test) 

        proc = VideoProcessorClient()
        proc.set_experiment_id(experiment_id)
        proc.start()
        
        #VideoProcessorProxy().start()
        
        return redirect(url_for('experiment.observe'))
    
    return render_template('control.html', form=form)

@bp.route('/toggle')
def toggle():
    video_processor = VideoProcessorClient()
    if video_processor.running:
        VideoProcessorClient().stop()
        return redirect(url_for('tracking.control'))
    else:
        experiment_id = "test"
        experiment_location = "home"
        # writing date, start time, experiment id, location to database
        write_in_experiment_parameters(experiment_id, experiment_location)
        VideoProcessorClient().start()
        
        return redirect(url_for('experiment.observe'))

@bp.route('/sync')
def sync():
    return jsonify(VideoProcessorClient().sync)


@bp.route('/feed')
def feed():
    return Response(VideoProcessorClient().generate_frame(), mimetype="multipart/x-mixed-replace; boundary=frame",
                    headers={'Cache-Control': 'no-store'})


class ExperimentInfoForm(Form):
    experiment_id = StringField('Experiment ID')
    experiment_location = StringField('Experiment location')
    experiment_test = BooleanField('Test?')

