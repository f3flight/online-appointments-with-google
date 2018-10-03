#!/usr/bin/env python
 
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
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
                message += '<input type="radio" name="slot" value="%s" />%s<br>' % (slot['id'], slot['start']['dateTime'])
            message += '<label for="name">Name:</label><input type="text" placeholder="John Doe" name="name" required/><br />'
            message += '<label for="phone">Phone:</label><input type="text" placeholder="+14081234567" name="phone" required/><br />'
            message += '<label for="email">Email:</label><input type="text" placeholder="abc@gmail.com" name="email"/><br />'
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
        bytedict = parse_qs(self.rfile.read(length), keep_blank_values=1)
        # bytedict structure: {b'key': [b'value'], ...}; not sure why so
        postvars = dict((k.decode("utf-8"), '' if not v else v[0].decode("utf-8")) for k, v in bytedict.items())
        if postvars['slot']:
            if not self.system.create_appointment(postvars['slot'], postvars):
                failed = True

        # Send response status code
        self.send_response(403 if failed else 200)
 
        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(bytes(str(fail_msg if failed else msg), "utf8"))
 
def run():
    print('starting server...')
 
    # Server settings
    # Choose port 8080, for port 80, which is normally used for a http server, you need root access
    server_address = ('127.0.0.1', 8888)
    httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
    print('running server...')
    httpd.serve_forever()
 
 
run()
