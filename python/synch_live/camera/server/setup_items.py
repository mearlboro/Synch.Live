import textwrap
from threading import Lock
from multiprocessing import SimpleQueue

from ansible_runner import Runner
from flask import Blueprint, url_for, redirect, render_template, current_app, get_template_attribute, \
    stream_with_context, Response, request
import ansible_runner
from wtforms import Form, SelectField


bp = Blueprint('setup_items', __name__, url_prefix='/setup_items')

status_queue = SimpleQueue()

lock = Lock()
_runner = None
_runner_process = None

@bp.route('/start', methods=['GET','POST'])
def start_setup():

    task = 'Waiting for task...'
    form = SetupTasks(request.form)

    if request.method == 'POST' and form.validate():

        if form.task.data == 'lights':
            playbook_name = 'test_lights.yml'
            task = 'Testing lights...'
            tags = 'rainbow'
        elif form.task.data == 'clocks':
            playbook_name = 'sync_time.yml'
            task = 'Synchronising clocks...'
            tags = None

        def event_handler(event):
            status_queue.put(event)

        def finished_callback(processor):
            lock.release()

        if not lock.locked():
            lock.acquire()
            global _runner, _runner_process
            (_runner_process, _runner) = ansible_runner.run_async(private_data_dir=current_app.config['ANSIBLE_DIR'],
                                                                playbook=playbook_name, forks=10, limit='players',
                                                                event_handler=event_handler,
                                                                tags=tags,
                                                                finished_callback=finished_callback)
                                                                
            
    return render_template('setup_items.html', form=form, task=task)


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
    if _runner is not None:
        _runner.cancel_callback = lambda: True
    return redirect(url_for('main'))

class SetupTasks(Form):
    task = SelectField('Setup task', choices=[('lights', 'Test lights'), ('clocks', 'Synchronise clocks')])
