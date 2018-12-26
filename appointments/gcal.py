from google.oauth2.service_account import Credentials as gcreds
from googleapiclient.discovery import build as gbuild

import copy
import datetime
import pytz
import re


class AppointmentManager(object):
    """Uses Google service account to create appointments w. Calendar API

       Attributes:
           tag_field (str): defines which field in Google calendar structure
               is used to store calendar's type and schedule name. The content
               of this field should not be modified by user.
           slots_tag (str): tag to indicate slot calendar.
           appointments_tag (str): tag to indicate appointments calendar.
           schedule_name (str): name of appointment schedule.
               Used as part of summary for generated calendars and events.
           timezone (str): schedule's timezone i.e. 'America/Los Angeles'.
           location (str): address of appointment, added into calendar event.
           admin (str): email of admin user (schedule owner). This user will
               be set as owner of the generated calendars and will see them
               in calendar list in Google Calendar.
           fixed_attendee (str): email to be added to all generated
               appointments (for example, service provider) to generate
               notifications about new appointments
           event_description (str): text put as description in generated
               appointments.
    """

    def __init__(self, creds_file, config=None):
        """Create AppointmentManager object

        Args:
            creds_file (str): path to service account's creds json.
                This file should be generated via Google API credentials page:
                https://console.developers.google.com/apis/credentials
            config (dict, optional): config dict, if provided is merged into
                object's attributes, allows to change any existing attribute.

        """

        # Below are defaults for all attributes. Change by passing config dict.
        self.tag_field = 'description'  # do not modify unnecessarily
        self.slots_tag = '#slots'  # do not modify unnecessarily
        self.appointments_tag = '#appointments'  # do not modify unnecessarily
        self.schedule_name = 'my services'
        self.timezone = 'America/Los_Angeles'
        self.location = '1 Nowhere street, 00000'
        self.admin = 'admin@admin.com'
        self.fixed_attendee = 'admin@admin.com'
        self.event_description = ('Looking forward to meeting you!'
                                  ' Need to change or cancel? Call/text me at'
                                  ' +12345678901')

        self.configure(config)

        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = gcreds.from_service_account_file(creds_file, scopes=SCOPES)

        self._api = gbuild('calendar', 'v3', credentials=creds)

        # the following section finds or creates slot and appointment calendars
        cals = self._api.calendarList().list().execute()
        slots_cal = None
        appointments_cal = None
        for cal in cals['items']:
            if cal.get(self.tag_field, '').startswith(self.slots_tag):
                slots_cal = cal['id']
            elif cal.get(self.tag_field, '').startswith(self.appointments_tag):
                appointments_cal = cal['id']
        if slots_cal:
            self.slots_cal = slots_cal
        else:
            self.slots_cal = self.create_cal(self.slots_tag, 'slots')
        if appointments_cal:
            self.appointments_cal = appointments_cal
        else:
            self.appointments_cal = self.create_cal(self.appointments_tag,
                                                    'appointments')
        # the following section sets bot's timezone
        # not sure yet if it helps with notifications, testing
        # problem is that notification to non-google emails have UTC time
        # in email
        primary_cal = self._api.calendars().get(calendarId='primary').execute()
        if primary_cal['timeZone'] != self.timezone:
            primary_cal['timeZone'] = self.timezone
            self._api.calendars().update(calendarId=primary_cal['id'],
                                         body=primary_cal).execute()
        self.refresh()

    def refresh(self):
        iso_now = '%s%s' % (datetime.datetime.now().isoformat('T'),
                            iso_tz(self.timezone))
        events = self._api.events()
        self.slots = events.list(calendarId=self.slots_cal,
                                 orderBy='startTime',
                                 singleEvents=True,
                                 timeMin=iso_now).execute()
        self.appointments = events.list(calendarId=self.appointments_cal,
                                        orderBy='startTime',
                                        singleEvents=True,
                                        timeMin=iso_now).execute()
        self.free_slots = self.get_free_slots()

    def configure(self, config_dict):
        if config_dict:
            for key, value in config_dict.items():
                if hasattr(self, key) and not key.startswith('_'):
                    setattr(self, key, value)

    def get_free_slots(self):
        free = copy.copy(self.slots['items'])
        for appointment in self.appointments['items']:
            i = 0
            while i < len(free):
                apnt_start = key_to_time(appointment, 'start')
                apnt_end = key_to_time(appointment, 'end')
                slot_start = key_to_time(free[i], 'start')
                slot_end = key_to_time(free[i], 'end')
                if apnt_start < slot_end and apnt_end > slot_start:
                    free.pop(i)
                    continue
                i += 1
        return free

    def create_cal(self, tag, name):
        body = {'summary': '%s - %s' % (self.schedule_name, name),
                'timeZone': self.timezone,
                'description': '%s %s' % (tag, self.schedule_name)}
        cal = self.api.calendars().insert(body=body).execute()
        body2 = {'scope': {'type': 'user', 'value': self.admin},
                 'role': 'owner'}
        self.api.acl().insert(calendarId=cal['id'], body=body2).execute()
        return cal['id']

    def create_appointment(self, chosen_slot_id, data):
        self.refresh()
        chosen_slot = None
        for slot in self.free_slots:
            if slot['id'] == chosen_slot_id:
                chosen_slot = slot
        if not chosen_slot:
            return False
        name = ' at '.join([data['name'], data['phone']])
        summary = '%s: %s' % (self.schedule_name, name)
        event = {'summary': summary,
                 'location': self.location,
                 'description': self.event_description,
                 'start': chosen_slot['start'],
                 'end': chosen_slot['end']}
        if getattr(self, 'fixed_attendee'):
            event['attendees'] = [{'email': self.fixed_attendee}]
        if data.get('email'):
            email = {'email': data['email']}
            if event.get('attendees'):
                event['attendees'].append(email)
            else:
                event['attendees'] = [email]
        result = self._api.events().insert(calendarId=self.appointments_cal,
                                           body=event,
                                           sendNotifications=True).execute()
        return result


def key_to_time(event, key_name):
    timestamp = event[key_name]['dateTime']
    # taken from https://stackoverflow.com/a/25878651/3952027
    # this regex removes all colons and all
    # dashes EXCEPT for the dash indicating + or - utc offset for the timezone
    conformed_timestamp = re.sub(r'[:]|([-](?!((\d{2}[:]\d{2})|(\d{4}))$))',
                                 '', timestamp)
    return datetime.datetime.strptime(conformed_timestamp, "%Y%m%dT%H%M%S%z")


def iso_tz(timezone_str):
    tz_now = datetime.datetime.now(pytz.timezone(timezone_str)).strftime('%z')
    # if ':' not in tz_now:
    #     tz_now =  '%s:%s' % (tz_now[:3], tz_now[3:])
    return tz_now
