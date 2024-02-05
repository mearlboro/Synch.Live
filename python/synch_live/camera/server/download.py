from flask import Blueprint, render_template, request, make_response
from wtforms import Form, StringField, SelectField

from synch_live.camera.db import process_query, get_all_experiment_ids_query

bp = Blueprint('download', __name__, url_prefix='/download')


@bp.route('/get_data')
def get_data():

    # sql query must be done outside of form in order to update dynamically in the app
    id_list = get_all_experiment_ids_query()
    form = DataInfoDropdown(request.args)
    form.experiment_id.choices = id_list
    

    if form.experiment_id.data and form.validate():
        
        experiment_id = form.experiment_id.data        

        response = process_query(experiment_id)

        response = make_response(response.getvalue())
        filename = f"SynchLive{experiment_id}"
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.csv'
        response.headers["Content-type"] = "text/csv"

        return response

    return render_template('data.html', form=form)


class DataInfoForm(Form):
    experiment_id = StringField('Experiment ID')


class DataInfoDropdown(Form):
    experiment_id = SelectField('Experiment ID')

