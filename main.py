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

BASE_DIR = pathlib.Path()
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
                self.send_html_file("index.html")
            case "/message.html":
                self.send_html_file("message.html")
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file("error.html", 404)


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

    # def render_template(self, filename, status=200):
    #     self.send_response(status)
    #     self.send_header('Content-type', 'text/html')
    #     self.end_headers()
    #     with open(BASE_DIR.joinpath('data/blog.json'), 'r', encoding='utf-8') as fd:
    #         r = json.load(fd)
    #     template = env.get_template(filename)
    #     print(template)
    #     html = template.render(blogs=r)
    #     self.wfile.write(html.encode())

    # def save_data_to_json(self, data):
    #     data_parse = urllib.parse.unquote_plus(data.decode())
    #     data_parse = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
    #     with open(BASE_DIR.joinpath('data/data.json'), 'w', encoding='utf-8') as fd:
    #         json.dump(data_parse, fd, ensure_ascii=False)


def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())

    value = {kay: value for kay, value in [el.split("=") for el in body.split("&")]}
    payload = {str(datetime.now()): value}
    try:
        with open(BASE_DIR.joinpath("storage/data.json"), "r", encoding="utf-8") as fd:
            old_data = json.load(fd)
    except FileNotFoundError:
        old_data = {}
    payload.update(old_data)
    with open(BASE_DIR.joinpath("storage/data.json"), "w", encoding="utf-8") as fd:
        json.dump(payload, fd, ensure_ascii=False, indent=2)


def run(server_class=HTTPServer, handler_class=HttpGetHandler):
    server_address = ('', 3000)
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
            # print(f'000000 11111111 Receive data {data}')
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
    # run()
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(SERV_IP, SERV_PORT))
    thread_socket.start()