#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it


import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse
import multiprocessing
import time

# Function to display help information
def help():
    print("httpclient.py [GET/POST] [URL]\n")

# Class representing an HTTP response
class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

# Class representing an HTTP client
class HTTPClient(object):
    # Method to establish a connection to the server
    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    # Method to extract the status code from the HTTP response
    def get_code(self, data):
        return int(data.split()[1])

    # Method to extract headers from the HTTP response
    def get_headers(self, data):
        headers = data.split('\r\n\r\n', 1)[0]
        return headers

    # Method to extract the body from the HTTP response
    def get_body(self, data):
        return data.split('\r\n\r\n', 1)[1]

    # Method to send data through the socket
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))

    # Method to close the socket connection
    def close(self):
        self.socket.close()

    # Read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    # Method to handle a GET request
    def GET(self, url, args=None):
        host, port, path, query = self.parse_url(url)
        self.connect(host, port)

        if query == '' and args is None:
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: me\r\nConnection: keep-alive\r\nAccept: */*\r\n\r\n"
        else:
            if args is None:
                query_part = query
            else:
                if isinstance(args, str):
                    query_part = args
                else:
                    query_part = urllib.parse.urlencode(args)
            request = f"GET {path}?{query_part} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: me\r\nConnection: keep-alive\r\nAccept: */*\r\n\r\n"

        self.sendall(request)

        # Introduce a delay for the specific host "slashdot.org"
        if host == "slashdot.org":
            time.sleep(1)

        self.socket.shutdown(socket.SHUT_WR)
        result = self.recvall(self.socket).strip()
        self.socket.close()
        code = self.get_code(result)
        body = self.get_body(result)
        print(result)
        return HTTPResponse(code, body)

    # Method to handle a POST request
    def POST(self, url, args=None):
        host, port = self.get_host_port(url)
        self.connect(host, port)

        if args:
            encoded_args = urllib.parse.urlencode(args)
        else:
            encoded_args = ""

        content_length = len(encoded_args)
        request = f"POST {url} HTTP/1.1\r\nHost: {host}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {content_length}\r\n\r\n{encoded_args}"
        self.sendall(request)
        data = self.recvall(self.socket)
        code = self.get_code(data)
        headers = self.get_headers(data)
        body = self.get_body(data)
        self.close()
        return HTTPResponse(code, body)

    # Method to parse the URL
    def parse_url(self, url):
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme != "http":
            raise ValueError("Error: no URL scheme provided")
        host = parsed_url.netloc.split(':')[0] if ':' in parsed_url.netloc else parsed_url.netloc
        port = int(parsed_url.netloc.split(':')[1]) if ':' in parsed_url.netloc else 80
        path = parsed_url.path if parsed_url.path else "/"
        query = parsed_url.query
        return host, port, path, query

    # Method to extract the host and port from the URL
    def get_host_port(self, url):
        parsed_url = urllib.parse.urlparse(url)
        host = parsed_url.netloc
        port = 80  # default HTTP port
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        return host, port

    # Method to execute the appropriate HTTP command
    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST(url, args)
        else:
            return self.GET(url, args)

# Class representing an HTTP client process
class HTTPClientProcess(multiprocessing.Process):
    def __init__(self, url, command, args=None):
        multiprocessing.Process.__init__(self)
        self.url = url
        self.command = command
        self.args = args

    # Method to run the HTTP client process
    def run(self):
        client = HTTPClient()
        if self.args:
            response = client.command(self.url, self.command, self.args)
        else:
            response = client.command(self.url, self.command)
        print(response.code)
        print(response.body)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        help()
        sys.exit(1)
    elif len(sys.argv) == 3:
        url, command = sys.argv[2], sys.argv[1]
        processes = []
        for _ in range(200):  # Adjust the number of processes based on your requirement
            process = HTTPClientProcess(url, command)
            process.start()
            processes.append(process)
        for process in processes:
            process.join()
    else:
        url = sys.argv[1]
        processes = []
        for _ in range(200):  # Adjust the number of processes based on your requirement
            process = HTTPClientProcess(url, "GET")
            process.start()
            processes.append(process)
        for process in processes:
            process.join()
