#!/usr/bin/env python3

try:
    from http.server import CGIHTTPRequestHandler, HTTPServer
except ImportError:
    from BaseHTTPServer import HTTPServer
    from CGIHTTPServer import CGIHTTPRequestHandler

handler = CGIHTTPRequestHandler
handler.cgi_directories = ['/']
server = HTTPServer(('localhost', 8080), handler)
server.serve_forever()
