from google.oauth2 import service_account
import googleapiclient.discovery
import yaml
import copy
import re
import datetime
import os

class AppointmentSystem(object):
    def __init__(self):
        config_file = 'config.yaml'
        tag_field = 'description' 
        slots_tag = '#slots'
        appointments_tag = '#appointments'
        self.schedule_name = 'my services'
        self.timezone = 'America/Los_Angeles'
        self.tz_str = '+00:00'
        self.location = '1 Nowhere street, 00000'
        self.admin = 'admin@admin.com'
        self.date_format = '%Y-%m-%d %H:%M'
        self.event_description = 'Looking forward to meeting you! Need to change or cancel? Call/text me at +12345678901'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.update(yaml.load(f))
        SCOPES=['https://www.googleapis.com/auth/calendar']
        SERVICE_ACCOUNT_FILE = 'credentials.json'
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE,
                                                                            scopes=SCOPES)
        self.api = googleapiclient.discovery.build('calendar','v3', credentials=credentials)
        cals = self.api.calendarList().list().execute()
        slots_cal = None
        appointments_cal = None
        for cal in cals['items']:
            if cal.get('description','').startswith(slots_tag):
                slots_cal = cal['id']
            elif cal.get('description','').startswith(appointments_tag):
                appointments_cal = cal['id']
                
        self.slots_cal = slots_cal if slots_cal else self.create_cal(slots_tag, 'slots')
        self.appointments_cal = appointments_cal if appointments_cal else self.create_cal(appointments_tag, 'appointments')
        self.refresh()
    
    def refresh(self):
        self.slots = self.api.events().list(calendarId=self.slots_cal,
                                            orderBy='startTime',
                                            singleEvents=True,
                                            timeMin=datetime.datetime.now().isoformat('T') + self.tz_str
                                            ).execute()
        self.appointments = self.api.events().list(calendarId=self.appointments_cal,
                                                   orderBy='startTime',
                                                   singleEvents=True,
                                                   timeMin=datetime.datetime.now().isoformat('T') + self.tz_str
                                                   ).execute()
        self.free_slots = self.get_free_slots()
        
    def update(self, config_dict):
        for key, value in config_dict.items():
            setattr(self, key, value)

    def get_free_slots(self):
        free_slots = copy.copy(self.slots['items'])
        for appointment in self.appointments['items']:
            i = 0
            while i < len(free_slots):
                if self.key_to_time(appointment, 'start') < self.key_to_time(free_slots[i], 'end'):
                    if self.key_to_time(appointment, 'end') > self.key_to_time(free_slots[i], 'start'):
                        free_slots.pop(i)
                        continue
                i += 1    
        return [dict(id=slot['id'], start=slot['start'], end=slot['end']) for slot in free_slots]
    
    def create_cal(self, tag, name):
        body = {'summary': '%s - %s' % (self.schedule_name, name), 'timeZone': self.timezone,
                'description': '%s %s' %(tag, self.schedule_name) }
        cal = self.api.calendars().insert(body=body).execute()
        body2 = {'scope': {'type': 'user', 'value': self.admin}, 'role': 'owner'}
        self.api.acl().insert(calendarId=cal['id'], body=body2).execute()
        return cal['id']
    
    @staticmethod
    def key_to_time(event, key_name):
        timestamp = event[key_name]['dateTime']
        # taken from https://stackoverflow.com/a/25878651/3952027
        # this regex removes all colons and all 
        # dashes EXCEPT for the dash indicating + or - utc offset for the timezone
        conformed_timestamp = re.sub(r"[:]|([-](?!((\d{2}[:]\d{2})|(\d{4}))$))", '', timestamp)
        return datetime.datetime.strptime(conformed_timestamp, "%Y%m%dT%H%M%S%z")    
        
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
            data['email'] = data['email'].replace(' ', '') # cleaning occasional spaces to prevent error
            if event.get('attendees'):
                event['attendees'].append(data)
            else:
                event['attendees'] = [data]
        self.api.events().insert(calendarId=self.appointments_cal, body=event, sendNotifications=True).execute()
        return True
        
    #print(len(slots['items']))
    
    #new_cal = api.calendars().insert(body=calendar).execute()
    
    #api.acl().insert(calendarId=new_cal['id'], body={'scope': {'type': 'user', 'value': admin}, 'role': 'owner'}).execute()
    
    #event = {'summary': 'domo arigato mista robato', 'location': 'Mars', 'description': 'say hello to the script =)', 'start': {'dateTime': '2018-10-10T15:00:00-07:00', 'timeZone': 'America/Los_Angeles'}, 'end': {'dateTime': '2018-10-10T17:00:00-07:00','timeZone': 'America/Los_Angeles'}, 'attendees': attendees}
    
    #api.events().insert(calendarId=new_cal['id'], body=event, sendNotifications=True).execute()
