import textwrap
from multiprocessing import SimpleQueue
from typing import Any

from array import array
from threading import Lock

from ansible_runner import Runner
from flask import Blueprint, url_for, redirect, render_template, current_app, get_template_attribute, \
    stream_with_context, Response, request
import ansible_runner

bp = Blueprint('setup', __name__, url_prefix='/setup')

_statuses = []
_status_queue = SimpleQueue()

_lock = Lock()
_runner = None
_runner_process = None

@bp.route('/start', methods=['GET', 'POST'])
def start_setup():
    global _statuses
    if request.method == 'POST':
        _statuses = []

        def event_handler(event):
            _status_queue.put(event)
            _statuses.append(event)

        def finished_callback(processor):
            _lock.release()

        if not _lock.locked():
            _lock.acquire()
            global _runner, _runner_process
            (_runner_process, _runner) = ansible_runner.run_async(private_data_dir=current_app.config['ANSIBLE_DIR'],
                                                                  playbook='setup.yml', forks=10, limit='players',
                                                                  event_handler=event_handler,
                                                                  finished_callback=finished_callback)

        return redirect(url_for('setup.start_setup'))
    return render_template('setup.html', statuses=_statuses)


@bp.route('/listen')
def messages():
    render_turbo_stream = get_template_attribute('_turbostreamhelpers.html', 'render_turbo_stream')

    def render_job(job):
        line = f'{job["stdout"]}\n'
        return render_turbo_stream('append', 'messages', caller=lambda: render_template('line.html', line=line))

    @stream_with_context
    def generate():
        while True:
            job = _status_queue.get()
            yield f'{textwrap.indent(render_job(job), "data: ", lambda line: True)}\n\n'
    return Response(generate(), mimetype="text/event-stream")


@bp.route('/stop', methods=['POST'])
def stop_setup():
    if _runner is not None:
        _runner.cancel_callback = lambda: True
    return redirect(url_for('main'))
