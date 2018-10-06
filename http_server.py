#!/usr/bin/env python

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import html
import ssl
import yaml
import os

import poc


# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):

    system = poc.AppointmentSystem()
    # GET
    def do_GET(self):
        self.system.refresh()
        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()

        # Send message back to client
        message = 'Please pick available slot:<br /><form action="/" method="post">'
        if not self.system.free_slots:
            message = 'Sorry, no slots are available for booking at this time! Try again later!'
        else:
            for slot in self.system.free_slots:
                message += '<input type="radio" name="slot" value="%s" />%s<br>' % (slot['id'], self.system.key_to_time(slot, 'start').strftime(self.system.date_format))
            message += '<label for="name">Name:</label><input type="text" placeholder="John Doe" name="name" required/><br />'
            message += '<label for="phone">Phone:</label><input type="text" placeholder="+14081234567" name="phone" required/><br />'
            message += '<label for="email">Email:</label><input type="email" placeholder="abc@gmail.com" name="email"/><br />'
            message += '<input type="submit" value="book" />'
        # message = "Hello world!"
        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))
        return

    def do_POST(self):
        failed = False
        msg = 'Appointment booked! Thank you!<br /><a href="/">Book some more...</a>'
        fail_msg = 'Sorry, this slot is already booked! Better luck next time!<br /><a href="/">Try again...</a>'
        length = int(self.headers['content-length'])
        bytedict = parse_qs(self.rfile.read(length))
        # bytedict structure: {b'key': [b'value'], ...}; not sure why so
        #with open('debug.log', 'a') as f:
        #    f.write('\n---POST:\n')
        #    f.write(yaml.dump(bytedict))
        postvars = dict((k.decode("utf-8"), html.unescape(v[0].decode("utf-8"))) for k, v in bytedict.items())
        if postvars.get('slot'):
            try:
                if not self.system.create_appointment(postvars['slot'], postvars):
                    failed = True
            except:
                failed = True
                if postvars['email']:
                    fail_msg = 'Something went wrong! Please check if your email is valid...<br /><a href="/">Try again...</a>'
                else:
                    fail_msg = 'Something went wrong! Please let us know about it and we will try to fix it asap.<br /><a href="/">Try again...</a>'
        else:
            failed = True
            fail_msg = 'Looks like you forgot to select a time slot?<br /><a href="/">Try again...</a>'

        # Send response status code
        self.send_response(500 if failed else 200)

        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(bytes(str(fail_msg if failed else msg), "utf8"))

def run():
    print('starting server...')

    # Server settings
    settings = {'address': '127.0.0.1',
                'port': 80,
                'ssl': False,
                'keyfile': None,
                'certfile': None}
    if os.path.exists('http_server.yaml'):
        with open('http_server.yaml', 'r') as f:
            settings.update(yaml.load(f))
    server_address = (settings['address'], settings['port'])
    httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
    if settings['ssl']:
        httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True, keyfile=settings['keyfile'], certfile=settings['certfile'])
    print('running server...')
    httpd.serve_forever()


run()
