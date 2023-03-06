import textwrap
from threading import Lock
from multiprocessing import SimpleQueue

from ansible_runner import Runner
from flask import Blueprint, url_for, redirect, render_template, current_app, get_template_attribute, \
    stream_with_context, Response
import ansible_runner

bp = Blueprint('setup', __name__, url_prefix='/setup')

status_queue = SimpleQueue()

lock = Lock()

@bp.route('/start')
def start_setup():
    def status_handler(status, runner_config):
        status_queue.put(status)

    def event_handler(event):
        status_queue.put(event)

    if not lock.locked():
        with lock:
            ansible_runner.run_async(private_data_dir=current_app.config['ANSIBLE_DIR'], playbook='setup.yml',
                                     forks=10, limit='players', event_handler=event_handler)
    return render_template('setup.html')


@bp.route('/listen')
def messages():
    render_turbo_stream = get_template_attribute('_turbostreamhelpers.html', 'render_turbo_stream')

    def render_job(job):
        line = f'{job["stdout"]}\n'
        return render_turbo_stream('append', 'messages', caller=lambda: render_template('line.html', line=line))

    @stream_with_context
    def generate():
        while True:
            job = status_queue.get()
            yield f'{textwrap.indent(render_job(job), "data: ", lambda line: True)}\n\n'
    return Response(generate(), mimetype="text/event-stream")


@bp.route('/stop')
def stop_setup():
    return redirect(url_for('main'))
