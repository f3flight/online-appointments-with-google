#!/usr/bin/env python

from flask import Flask
app = Flask(__name__)

import html
import ssl
import yaml
import os

from appointments import gcal
from googleapiclient.errors import HttpError

from flask import g
from flask import request


cfg = {} if not os.path.exists('config.yaml') else yaml.load(open('config.yaml', 'r'))

@app.route('/', methods=['GET', 'POST'])
def main():
    if 'cal' not in g:
        g.cal = gcal.AppointmentManager('credentials.json', cfg)
    if request.method == 'GET':
        return get()
    else:
        return post(request)


def get():
    date_format = '%B %d, %a %-I:%M%p'
    g.cal.refresh()

    # Send message back to client
    message = 'Please pick available slot:<br /><form action="/" method="post">'
    if not g.cal.free_slots:
        message = 'Sorry, no slots are available for booking at this time! Try again later!'
    else:
        for slot in g.cal.free_slots:
            message += '<input type="radio" name="slot" value="%s" />%s<br>' % (slot['id'], gcal.key_to_time(slot, 'start').strftime(date_format))
        message += '<label for="name">Name:</label><input type="text" placeholder="John Doe" name="name" required/><br />'
        message += '<label for="phone">Phone:</label><input type="text" placeholder="+14081234567" name="phone" required/><br />'
        message += '<label for="email">Email:</label><input type="email" placeholder="abc@gmail.com" name="email"/><br />'
        message += '<input type="submit" value="book" />'
    return message


def post(request):
    ok = True
    msg = 'Appointment booked! Thank you!<br /><a href="/">Book some more...</a>'
    fail_msg = 'Sorry, this slot is already booked! Better luck next time!<br /><a href="/">Try again...</a>'
    if request.form.get('slot'):
        try:
            ok = g.cal.create_appointment(request.form['slot'], request.form)
        except HttpError as e:
            ok = False
            fail_msg = 'Something went wrong! '
            fail_msg += 'Error details: < %s | %s | %s >' % (e.resp.status, e.resp.reason, e._get_reason())
            fail_msg += '<br /><a href="/">Try again...</a>'
    else:
        ok = False
        fail_msg = 'Looks like you forgot to select a time slot?<br /><a href="/">Try again...</a>'

    return msg if ok else fail_msg
