from flask import Blueprint, url_for, redirect, render_template

bp = Blueprint('setup', __name__, url_prefix='/setup')


@bp.route('/start')
def start_setup():
    return render_template('setup.html')


@bp.route('/stop')
def stop_setup():
    return redirect(url_for('main'))
