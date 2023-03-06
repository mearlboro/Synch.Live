from copy import deepcopy
from types import SimpleNamespace

import yaml
from flask import Blueprint, redirect, url_for, Response, jsonify, render_template, request, flash
from markupsafe import Markup
from wtforms import Form, StringField, BooleanField, widgets, IntegerField, validators, FormField, SelectField
from wtforms.widgets import html_params

from synch_live.camera.tools.colour import hsv_to_hex, hex_to_hsv
from synch_live.camera.tools.config import parse, unwrap_hsv, unparse
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
        proc.experiment_id = experiment_id
        proc.start()

        return redirect(url_for('experiment.observe'))
    
    return render_template('control.html', form=form, tab='control')


@bp.route('/toggle')
def toggle():
    video_processor = VideoProcessorClient()
    if video_processor.running:
        VideoProcessorClient().stop()
        return redirect(url_for('tracking.control'))
    else:
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


def calibration_form(config):
    if config.server.CAMERA == 'pi':
        return PiCalibrationForm(request.form, config)
    else:
        return CalibrationForm(request.form, config)


@bp.route('/calibrate', methods=['GET', 'POST'])
def calibrate():
    video_processor = VideoProcessorClient()
    form = calibration_form(video_processor.config)
    if request.method == 'POST' and form.validate():
        if form.save_config.data.get('save_file'):
            save_config(form.save_config.data.get('conf_path'))
        form.__delitem__('save_config')
        config = SimpleNamespace(**video_processor.config.__dict__)
        form.populate_obj(config)
        video_processor.config = config

        flash('Calibration complete!')
        return redirect(url_for('tracking.calibrate'))
    return render_template('control.html', form=form, tab='calibrate')


def save_config(conf_path):
    file = open(conf_path, 'w')
    conf_to_save = deepcopy(VideoProcessorClient().config)
    conf_to_save.detection.min_colour = parse(unwrap_hsv(conf_to_save.detection.min_colour))
    conf_to_save.detection.max_colour = parse(unwrap_hsv(conf_to_save.detection.max_colour))
    delattr(conf_to_save, 'conf_path')
    yaml.dump(unparse(conf_to_save), file)


class ColorField(StringField):
    widget = widgets.ColorInput()

    def _value(self):
        return hsv_to_hex(self.data.__dict__) if self.data is not None else ''

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0] is not None:
            self.data = parse(hex_to_hsv(valuelist[0]))


class SaveConfigForm(Form):
    save_file = BooleanField('Save to file')
    conf_path = StringField('Path', default=lambda: VideoProcessorClient().config.conf_path)


class FieldsetWidget:
    def __call__(self, field, fieldset_kwargs=None, legend_kwargs=None, ul_kwargs=None, li_kwargs=None,
                 label_kwargs=None, errors_caller=None, **kwargs):
        if fieldset_kwargs is None:
            fieldset_kwargs = dict()
        if legend_kwargs is None:
            legend_kwargs = dict()
        if ul_kwargs is None:
            ul_kwargs = dict()
        if li_kwargs is None:
            li_kwargs = dict()
        if label_kwargs is None:
            label_kwargs = dict()
        kwargs.setdefault("id", field.id)
        html = [f"<fieldset {html_params(**fieldset_kwargs)}>"
                f"<legend {html_params(**legend_kwargs)}>{field.label.text}</legend>"
                f"<ul {html_params(**ul_kwargs)}>"]
        for subfield in field:
            html.append(f"<li {html_params(**li_kwargs)}>{subfield.label(**label_kwargs)} {subfield(**kwargs)}")
            if errors_caller is not None:
                html.append(errors_caller(subfield.errors))
            html.append("</li>")
        html.append("</ul>")
        html.append("</fieldset>")
        return Markup("".join(html))


class TrackingForm(Form):
    max_players = IntegerField('Players to track', [validators.number_range(min=3)])


class DetectionForm(Form):
    min_contour = IntegerField('Minimum contour length', [validators.number_range(min=10, max=200)])
    max_contour = IntegerField('Maximum contour length', [validators.number_range(min=10, max=1000)])
    min_colour = ColorField('Minimum tracking colour')
    max_colour = ColorField('Maximum tracking colour')


class CalibrationForm(Form):
    tracking = FormField(TrackingForm, widget=FieldsetWidget())
    detection = FormField(DetectionForm, widget=FieldsetWidget())
    save_config = FormField(SaveConfigForm, widget=FieldsetWidget())


class CameraCalibrationForm(Form):
    iso = IntegerField('ISO', [validators.number_range(min=25, max=800)])
    shutter_speed = IntegerField('Shutter speed', [validators.number_range(min=244, max=1000000)])
    saturation = IntegerField('Saturation', [validators.number_range(min=-100, max=100)])
    awb_mode = SelectField('Auto white balance mode', choices=[
        "off",
        "auto",
        "sunlight",
        "cloudy",
        "shade",
        "tungsten",
        "fluorescent",
        "incandescent",
        "flash",
        "horizon",
        "greyworld"
    ])


class PiCalibrationForm(CalibrationForm):
    camera = FormField(CameraCalibrationForm, widget=FieldsetWidget())
