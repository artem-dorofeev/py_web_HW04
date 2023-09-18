import pathlib
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import mimetypes
import json
import socket
import logging
from threading import Thread
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

BASE_DIR = pathlib.Path('html-data')
# print(f'14 - base_dir - {BASE_DIR}')
BUFFER = 1024
SERV_IP = '127.0.0.1'
SERV_PORT = 5000
env = Environment(loader=FileSystemLoader('templates'))


def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERV_IP, SERV_PORT))
    # print(f"0000000 11111111 Send data {body}")
    client_socket.close()


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(body)
        self.send_response(302)
        self.send_header('Location', '/index.html')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)

        match route.path:
            case "/":
                self.send_html_file('html-data/index.html')
            case "/message.html":
                self.send_html_file('html-data/message.html')
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file('html-data/error.html', 404)


    def send_static(self, file):
        self.send_response(200)
        mt, *rest = mimetypes.guess_type(file)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(file, 'rb') as fd:  # ./assets/js/app.js
            self.wfile.write(fd.read())

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fb:
            self.wfile.write(fb.read())



def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())
    # print(f'74  {data}')

    value = {kay: value for kay, value in [el.split("=") for el in body.split("&")]}
    payload = {str(datetime.now()): value}
    try:
        with open(BASE_DIR.joinpath("storage/data.json"), "r", encoding="utf-8") as fd:
            # print(f'80 try, base_dir - {BASE_DIR}')
            old_data = json.load(fd)
    except FileNotFoundError:
        old_data = {}
    payload.update(old_data)
    with open(BASE_DIR.joinpath("storage/data.json"), "w", encoding="utf-8") as fd:
        # print(f'86 try, base_dir - {BASE_DIR}')
        json.dump(payload, fd, ensure_ascii=False, indent=2)


def run(server_class=HTTPServer, handler_class=HttpGetHandler):
    server_address = ('0.0.0.0', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            data, address = server_socket.recvfrom(BUFFER)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
    STORAGE_DIR = pathlib.Path().joinpath('html-data/storage')
    FILE_STORAGE = STORAGE_DIR / 'data.json'

    # print(113, STORAGE_DIR, FILE_STORAGE)
    if not FILE_STORAGE.exists():

        with open(FILE_STORAGE, "w", encoding="utf-8") as fd:
            json.dump({}, fd, ensure_ascii=False, indent=2)

    # run()
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(SERV_IP, SERV_PORT))
    thread_socket.start()

    """BASE_DIR.joinpath("storage/data.json"""