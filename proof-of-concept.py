from google.oauth2 import service_account
import googleapiclient.discovery

SCOPES=['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = '/root/credentials.json'
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
api = googleapiclient.discovery.build('calendar','v3', credentials=credentials)

calendar = {'summary': 'testCalendar', 'timeZone': 'America/Los_Angeles'}

admin = 'f3flight@gmail.com'
attendees = [{'email': 'elenabrzezinski@gmail.com'}]

new_cal = api.calendars().insert(body=calendar).execute()

api.acl().insert(calendarId=new_cal['id'], body={'scope': {'type': 'user', 'value': admin}, 'role': 'owner'}).execute()

event = {'summary': 'domo arigato mista robato', 'location': 'Mars', 'description': 'say hello to the script =)', 'start': {'dateTime': '2018-10-10T15:00:00-07:00', 'timeZone': 'America/Los_Angeles'}, 'end': {'dateTime': '2018-10-10T17:00:00-07:00','timeZone': 'America/Los_Angeles'}, 'attendees': attendees}

api.events().insert(calendarId=new_cal['id'], body=event, sendNotifications=True).execute()
