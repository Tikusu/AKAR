#!/usr/bin/env python3
"""AKAR static launcher. Python standard library only; no database or packages."""
import argparse
import functools
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / '.runtime'
STATE = RUNTIME / 'server.json'
IDENTITY = hashlib.sha256(str(ROOT).encode()).hexdigest()[:24]


def running():
    try:
        data = json.loads(STATE.read_text())
        port = int(data['port'])
        if not 1024 <= port <= 65535:
            return None
        with urllib.request.urlopen('http://127.0.0.1:%d/__akar_health' % port, timeout=1) as response:
            health = json.load(response)
        return data if health.get('identity') == IDENTITY else None
    except (OSError, ValueError, KeyError):
        return None


def open_browser(url):
    command = shutil.which('termux-open-url')
    if not command:
        candidate = '/data/data/com.termux/files/usr/bin/termux-open-url'
        if Path(candidate).is_file():
            command = candidate
    try:
        if command:
            subprocess.Popen([command, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == 'win32':
            os.startfile(url)
        elif os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
            webbrowser.open(url)
        else:
            print('Browser tidak tersedia di terminal ini. Buka URL di atas pada perangkat yang sama.')
    except OSError:
        print('Buka alamat di atas secara manual pada browser.')


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        if path == '/__akar_health':
            data = json.dumps({'identity': IDENTITY, 'app': 'AKAR'}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if any(part.startswith('.') for part in path.split('/') if part):
            self.send_error(404)
            return
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404, 'Folder listing disabled')
        return None

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-transform')
        super().end_headers()


def serve():
    RUNTIME.mkdir(exist_ok=True)
    handler = functools.partial(Handler, directory=str(ROOT))
    preferred = int(os.environ.get('AKAR_PORT', '5177'))
    try:
        server = ThreadingHTTPServer(('127.0.0.1', preferred), handler)
    except OSError:
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    port = server.server_address[1]
    data = {'pid': os.getpid(), 'port': port, 'url': 'http://127.0.0.1:%d/' % port}
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(data))
    temporary.replace(STATE)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        try:
            if json.loads(STATE.read_text()).get('pid') == os.getpid():
                STATE.unlink()
        except (OSError, ValueError):
            pass


def start(no_open=False):
    data = running()
    if not data:
        if not (ROOT / 'index.html').is_file():
            raise SystemExit('index.html tidak ditemukan. Ekstrak seluruh isi ZIP terlebih dahulu.')
        RUNTIME.mkdir(exist_ok=True)
        with (RUNTIME / 'server.log').open('a') as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--serve'],
                                       cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                       start_new_session=True)
        for _ in range(50):
            data = running()
            if data:
                break
            if process.poll() is not None:
                raise SystemExit('Server gagal dimulai. Periksa .runtime/server.log.')
            time.sleep(.2)
        if not data:
            process.terminate()
            raise SystemExit('Server belum siap. Periksa .runtime/server.log.')
    print('\nAKAR siap: %s\nWeb statis lokal. Tidak memerlukan MySQL, PHP, atau npm.\n' % data['url'])
    if not no_open:
        open_browser(data['url'])


def stop():
    data = running()
    if data:
        import signal
        os.kill(int(data['pid']), signal.SIGTERM)
        STATE.unlink(missing_ok=True)
        print('Server AKAR dihentikan.')
    else:
        print('Tidak ada server AKAR aktif untuk folder ini.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--stop', action='store_true')
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args()
    if args.serve:
        serve()
    elif args.stop:
        stop()
    else:
        start(args.no_open)
