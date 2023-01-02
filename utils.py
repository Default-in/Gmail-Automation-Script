from gmail_constants import *
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime


def get_existing_emails_from_sheet():
    gsheet_client = gsheet_setup()
    email_ids_worksheet = gsheet_client.open_by_url(GMAIL_SHEET_INFO['sheet_url']).worksheet(GMAIL_SHEET_INFO['email_ids_worksheet'])
    existing_email_list = email_ids_worksheet.col_values(1)
    existing_email_list = existing_email_list[1:] # Remove header
    return existing_email_list

    
def append_to_sheet(data_to_write,sheet_url,worksheetname):
        client = gsheet_setup()
        worksheet = client.open_by_url(sheet_url).worksheet(worksheetname)
        worksheet.append_rows(data_to_write)
        
def extract_date(date_str):
    only_date = date_str.split(' ')[0]
    split_date = only_date.split('-')   
    return split_date[0]+"/"+split_date[1]+"/"+split_date[2]

def get_val_from_row_col(row,col,sheet_url,worksheet):
    client = gsheet_setup()
    spreadsheet = client.open_by_url(sheet_url).worksheet(worksheet)    
    return spreadsheet.cell(row,col).value

def find_cell_row_col(value,sheet_url,worksheet):
    client = gsheet_setup()
    spreadsheet = client.open_by_url(sheet_url).worksheet(worksheet)
    try :
        cell = spreadsheet.find(value)
        return [cell.row,cell.col]
    except Exception as e :
        return None

def gsheet_setup():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GSHEET_CREDENTIALS, GSHEET_SCOPES)
    client = gspread.authorize(credentials)

    return client

def seperate_email_id(email_obj):
    # email_obj is in the form account name <email_id for account>
    # So we need only what is in between < and >
    if '<' in email_obj:
        index_of_left_angular = email_obj.index('<')
        index_of_email_id = index_of_left_angular+1
        email_id = email_obj[index_of_email_id:len(email_obj)-1]
        return email_id
    else :
        return None 

def tn():
    return datetime.datetime.now()

def update_date_in_sheet(change,row,col):
    client = gsheet_setup()
    worksheet = client.open_by_url(GMAIL_SHEET_INFO['sheet_url']).worksheet(GMAIL_SHEET_INFO['email_ids_worksheet'])
    worksheet.update_cell(row,col,change)
    
def post_processing(email_ids,sheet_url,worksheet):
    existing_emails_in_sheet = set(get_existing_emails_from_sheet())
    
    new_emails = email_ids.difference(existing_emails_in_sheet) # Set difference 
       
    new_emails = list(new_emails)
    
    new_emails_list_of_list = []
    
    for email in new_emails :
        row_list = [email]
        new_emails_list_of_list.append(row_list)
    
    append_to_sheet(new_emails_list_of_list,sheet_url,worksheet)

def setup_gmail_api():
    creds = None
    if os.path.exists(GMAIL_API_TOKEN_LOCATION):
        creds = Credentials.from_authorized_user_file(GMAIL_API_TOKEN_LOCATION, GMAIL_SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_API_CREDENTIALS_LOCATION, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GMAIL_API_TOKEN_LOCATION, 'w') as token:
            token.write(creds.to_json())
    try : 
        service = build('gmail', 'v1', credentials=creds)
        print("Gmail Service Created Successfully")
        return service
    except Exception as e : 
        message = f"Error occured while setting up gmail API - {e}"
        return None