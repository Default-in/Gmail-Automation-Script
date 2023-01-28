from gmail_constants import *
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import base64
import os
import json
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def get_existing_emails_from_sheet():
    gsheet_client = gsheet_setup()
    email_ids_worksheet = gsheet_client.open_by_url(GMAIL_SHEET_INFO['sheet_url']).worksheet(GMAIL_SHEET_INFO['email_ids_worksheet'])
    existing_email_list = email_ids_worksheet.col_values(1)
    existing_email_list = existing_email_list[1:] # Remove header
    return existing_email_list


def write_to_json(dict_to_write):
    with open('body.json','w') as fp:
        json.dump(dict_to_write,fp)

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
    
def decode_base_64_string(ip):
    decoded = base64.b64decode(ip)
    return decoded

def email_ids_from_dict(email_dict):
    email_ids = set()
    try :
        payload = email_dict['payload']
        headers = payload['headers']
                
        for d in headers:                
                if d['name']=="Bcc" or d['name']=="Cc" or d['name']=="From" or d['name']=='To':
                    splitted_emails = d['value'].split(',') 
                    
                    for em in splitted_emails :
                        # As per data observed,only 2 types of data is received for now
                        
                        # 1) Account name <emailid_associated> 2) email_id
                        if '<' in em:
                            email_id = seperate_email_id(em)
                            if email_id :                                 
                                email_ids.add(email_id)
                        else :
                            email_ids.add(em)
    except Exception as e:
        error_message = f"Error occured in getting email id from dictionary - {e}"
        print(error_message)
    
    return list(email_ids)