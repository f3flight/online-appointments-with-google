INITIAL GOALS - This web app (when finished) should allow after installation:

1. create 2 calendars: timetable calendar and appointments calendar
2. set owner, i.e. allow some user to manage both calendars
3. method which gets future events from both calendars and substracts appointments from timetable - result is list of free slots
4. web page which presents list of free slots for selection, with fields for name, phone, email
5. when submitted, check again if slot is free, then create event in appointments calendar, filling details and attendee with specified info

PREREQUISITES:

1. https://console.developers.google.com/cloud-resource-manager # create a project
2. https://console.developers.google.com/apis/dashboard # find and enable Calendar API
2.1. alternatively direct link to API page - https://console.developers.google.com/apis/library/calendar-json.googleapis.com # press ENABLE
3. https://console.developers.google.com/apis/credentials
3.1 create credentials -> service account key -> new sevice account -> select role Project->Owner, key type = json, CREATE
3.2 save file as `credentials.json`, move to repo folder
