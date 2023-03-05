from flask import Blueprint, render_template, request, make_response
from wtforms import Form, IntegerField, validators, StringField, widgets, SelectField, BooleanField, FormField
from wtforms.widgets import html_params

from synch_live.camera.server.db import *

bp = Blueprint('download', __name__, url_prefix='/download')

@bp.route('/get_data', methods=['GET','POST'])
def get_data():
    
    #form = DataInfoForm(request.form)
    id_list = get_all_experiment_ids_query()
    form = DataInfoDropdown(request.form)
    form.experiment_id.choices = id_list
    
    if request.method == 'POST' and form.validate():

        experiment_id = form.experiment_id.data        

        response = process_query(experiment_id)

        response = make_response(response.getvalue())
        filename = "SynchLive" + experiment_id
        response.headers['Content-Disposition'] = 'attachment; filename=' + filename + '.csv'
        response.headers["Content-type"] = "text/csv"

        return response

    #return render_template('data.html', form=form)
    return render_template('data.html', form=form)

class DataInfoForm(Form):
    experiment_id = StringField('Experiment ID')

class DataInfoDropdown(Form):
    experiment_id = SelectField('Experiment ID')

