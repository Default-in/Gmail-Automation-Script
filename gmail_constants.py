GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
GMAIL_API_TOKEN_LOCATION = 'token.json'

GMAIL_API_CREDENTIALS_LOCATION = 'gmail_credentials.json'
GMAIL_USER_ID = 'harpritsinh@getdefault.in' # Have to ask Varun sir about the input like should it be dynamic or hardcoded constant
GMAIL_SHEET_INFO = {
    'sheet_url':"https://docs.google.com/spreadsheets/d/1eDt8fP4eYIj5yDVoVFJ26mitap2DF3lxW_T_JwgLtZo/edit#gid=0",
    'last_run_worksheet':'Script Last Run',
    'email_ids_worksheet':'Emails'
}
GSHEET_CREDENTIALS = 'googlesheet.json'
GMAIL_EMAIL_TYPES = ['sent','inbox']
GMAIL_LABELS = {
    'sent':'SENT',
    'inbox':'INBOX'
}
GMAIL_MAX_RESULTS = 500 #As per Gmail API for now,might change in future
GSHEET_SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]