import textwrap
from queue import SimpleQueue

from flask import Blueprint, Response, g, current_app, get_template_attribute, render_template, stream_with_context
from zeroconf import ServiceListener, Zeroconf, ServiceBrowser

bp = Blueprint('players_listener', __name__, url_prefix='/players')


@bp.route('/listen')
def live_players():
    zeroconf = Zeroconf()
    queue = SimpleQueue()
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", PlayerListener(queue))
    render_turbo_stream = get_template_attribute('_turbostreamhelpers.html', 'render_turbo_stream')

    def render_job(job):
        if job['action'] == 'replace':
            target = f'player_{job["player_id"]}'
        else:
            target = 'players'
        return render_turbo_stream(job['action'], target,
                                   caller=lambda: render_template('player_link.html', player=dict(
                                       id=job['player_id'],
                                       href=f'http://{job["host"]}:{job["port"]}',
                                       caption=f'Player {job["player_id"]}'
                                   )))

    @stream_with_context
    def generate():
        try:
            while True:
                job = queue.get()
                yield f'{textwrap.indent(render_job(job), "data: ", lambda line: True)}\n\n'
        finally:
            browser.cancel()
            zeroconf.close()
    return Response(generate(), mimetype="text/event-stream")


class PlayerListener(ServiceListener):
    def __init__(self, queue: SimpleQueue):
        self.queue = queue

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if not info.server.startswith("player"):
            return
        name = info.server.rstrip(".local")
        player_id = name.lstrip("player")
        self.queue.put(dict(name=name, action='replace', host=info.server, port=info.port,
                            player_id=player_id))

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if not info.server.startswith("player"):
            return
        name = info.server.rstrip(".local")
        player_id = name.lstrip("player")
        self.queue.put(dict(name=name, action='remove', host=info.server, port=info.port,
                            player_id=player_id))

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if not info.server.startswith("player"):
            return
        name = info.server.rstrip(".local")
        player_id = name.lstrip("player")
        self.queue.put(dict(name=name, action='append', host=info.server, port=info.port,
                            player_id=player_id))
