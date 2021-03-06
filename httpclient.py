#!/usr/bin/env python
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
import urllib

def help():
    print "httpclient.py [GET/POST] [URL]\n"

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):

    def connect(self, host, port):
        # use sockets!
        try:
            ipAddress = socket.gethostbyname(host)
        except socket.gaierror:
            print 'Cannot not find hostname. Exiting'
            sys.exit(1)
        try:
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, errNo:
            print 'Socket creation failed. Error code: ' + str(errNo[0]) +\
                ', Error message: ' + errNo[1]
            sys.exit(1)

        connection.connect((ipAddress, port))
        return connection

    def get_code(self, data):
        httpCode = 500
        if data.startswith('HTTP/1.'):
            httpCode = int(data[9:12])
        return httpCode

    def get_headers(self,data):
        httpHeaders = None
        endLocation = data.find("\r\n\r\n")

        if endLocation != -1:
            httpHeaders = data[:endLocation]

        return httpHeaders

    def get_body(self, data):
        httpBody = None
        endLocation = data.find("\r\n\r\n")

        if endLocation != -1:
            httpBody = data[endLocation + 4:]
        return httpBody

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return str(buffer)

    def GET(self, url, args=None):
        code = 500
        body = ""

        path, host, port = self.get_path_host_port(url)

        connection = self.connect(host, port)

        headers = {
            "User-Agent": "WebClient",
            "Host": host,
            "Accept": "*/*"
        }
        try:
            connection.sendall(self.requestString("GET", path, headers))
        except socket.error:
            print "GET request sendall() failed."
            sys.exit(1)
        connection.shutdown(socket.SHUT_WR)

        recv = self.recvall(connection)
        code = self.get_code(recv)
        body = self.get_body(recv)

        connection.close()
        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        code = 500
        body = ""
        var = ""

        path, host, port = self.get_path_host_port(url)

        connection = self.connect(host, port)

        headers = {
            "User-Agent": "WebClient",
            "Host": host,
            "Accept": "*/*",
            "Content-Length": "0",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        if args:
            var = urllib.urlencode(args)
            headers["Content-Length"] = str(len(var))

        try:
            connection.sendall(self.requestString("POST", path, headers)+ var)
        except socket.error:
            print "POST request sendall() failed."
            sys.exit(1)
        connection.shutdown(socket.SHUT_WR)

        recv = self.recvall(connection)
        code = self.get_code(recv)
        body = self.get_body(recv)

        connection.close()
        
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        try:
            if (command == "POST"):
                return self.POST( url, args )
            else:
                return self.GET( url, args )
        except socket.timout:
            print "Request timed out."

    def get_path_host_port(self, url):
        port = 80
        
        if url.startswith("http://"):
            url = url[7:]

        slashLoc = url.find('/')
        host = url

        if slashLoc == -1:
            path = '/'
        else:
            path = url[slashLoc:]
            host = url[:slashLoc]

        colonLoc = host.find(':')

        if colonLoc != -1:
            try:
                port = int(host[colonLoc + 1:])
            except ValueError:
                print "Provided port is not a valid integer"
                sys.exit(1)
            if (port < 0) or (port > 65535):
                print "Port is outside of allowable range. (0-65535)"
                sys.exit(1)
            host = host[:colonLoc]
        return path, host, port

    def requestString(self, command, path, headers):
        requestStr = command + " " + path + " " + "HTTP/1.1\r\n"

        for header in headers.keys():
            requestStr += header + ": " + headers[header] + "\r\n"
        requestStr += "\r\n"

        return requestStr

if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print client.command( sys.argv[2], sys.argv[1] )
    else:
        print client.command( sys.argv[1] )
