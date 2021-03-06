#!/usr/bin/env python

from flask import Flask
app = Flask(__name__)

import html
import json
import ssl
import yaml
import os

from appointments import gcal
from googleapiclient.errors import HttpError

from flask import g
from flask import request


cfg = {} if not os.path.exists('config.yaml') else yaml.load(open('config.yaml', 'r'))
html_cfg = {} if not os.path.exists('html_config.yaml') else yaml.load(open('html_config.yaml', 'r'))

@app.route('/', methods=['GET', 'POST'])
def main():
    if 'cal' not in g:
        g.cal = gcal.AppointmentManager('credentials.json', cfg)
    if request.method == 'GET':
        return get()
    else:
        return post(request)

@app.route('/free')
def free_json():
    if 'cal' not in g:
        g.cal = gcal.AppointmentManager('credentials.json', cfg)
    return json.dumps(free_slots_stripped())

def free_slots_stripped():
    result = {}
    for slot in g.cal.free_slots:
        result[slot['start']['dateTime']] = { 'id': slot['id'],
                                              'end': slot['end']['dateTime']}
    return result

def get():
    date_format = '%B %d, %a %-I:%M%p'
    g.cal.refresh()

    # Send message back to client
    message = ('<head><title>%s</title>%s%s%s%s'
               % (cfg['schedule_name'],
                  '<link href="/static/rome.css" rel="stylesheet" type="text/css" />',
                  '<script src="/static/rome.js"></script>',
                  '<script src="/static/draft_code.js"></script>',
                  '<script>const dates = ' + json.dumps(free_slots_stripped()) + '</script>'))
    if os.path.exists('static/googleanalytics.html'):
        message += open('static/googleanalytics.html', 'r').read()
    message += '</head><body onload="init()"><h3>%s - appointment scheduler</h3>' % cfg['schedule_name']
    if 'some_text' in html_cfg:
        message += html_cfg['some_text']
    if not g.cal.free_slots:
        message += 'Sorry, no slots are available for booking at this time! Try again later!</body>'
    else:
        message += '<div id="calendar"></div><br />'
        message += '<div id="message">Please pick from available dates above ^^</div><br />'
        message += '<form method="post"><div id="slots"></div>'
        message += '</body>'
    return message


def post(request):
    ok = True
    msg = 'Appointment booked! Thank you!<br /><a href=".">Book some more...</a>'
    fail_msg = 'Sorry, this slot is already booked! Better luck next time!<br /><a href=".">Try again...</a>'
    if request.form.get('slot'):
        try:
            ok = g.cal.create_appointment(request.form['slot'], request.form)
        except HttpError as e:
            ok = False
            fail_msg = 'Something went wrong! '
            fail_msg += 'Error details: < %s | %s | %s >' % (e.resp.status, e.resp.reason, e._get_reason())
            fail_msg += '<br /><a href=".">Try again...</a>'
    else:
        ok = False
        fail_msg = 'Looks like you forgot to select a time slot?<br /><a href=".">Try again...</a>'

    return msg if ok else fail_msg
