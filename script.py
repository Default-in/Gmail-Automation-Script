import time
from gmail_constants import *  
from utils import *
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json
from google_auth_oauthlib.flow import InstalledAppFlow
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import os
import datetime

# Approach : In order to avoid excess Gmail API calls by fetching each and every email,
# I have done implementation in such a way that only emails after the last script run should be fetched
# Suppose if script was run 5 days ago and fetched 4000 email ids then if script is running today it doesn't need to fetch those 4000 emails
# Instead script should fetch emails from the last run script date   

# For this I am maintaing a seperate worksheet where for each user who runs this script,the date will be noted    

def get_labels(gmail_service):
    label_res = gmail_service.users().labels().list(userId=GMAIL_USER_ID).execute()
    label_res = label_res.get('labels',[])
    label_list = []
    
    for label in label_res :
        label_list.append(label['name'])
    return label_list

def get_message_from_id(gmail_service,msgid):
    msg = None
    try :
        msg = gmail_service.users().messages().get(userId=GMAIL_USER_ID,id=msgid).execute()
    except Exception as e :
        error_message = f"Error occured in getting message from id : {e}"
        print(error_message)
    return msg

def get_all_required_emails_messages(gmail_service,label=None,query=None):
    if label is None : 
        label = GMAIL_LABELS['inbox']
    try :
        if query :
            emails_results = gmail_service.users().messages().list(userId=GMAIL_USER_ID,labelIds=[label],q=query,maxResults=GMAIL_MAX_RESULTS).execute()
        else:
            emails_results = gmail_service.users().messages().list(userId=GMAIL_USER_ID,labelIds=[label],maxResults=GMAIL_MAX_RESULTS).execute()
        emails_results_msgs = emails_results.get('messages',[])
    except Exception as e :
        error_message = f"Error occured in getting emails of label - {e}"
        print(error_message)
        return None
    
    while True:
        msgs = set()
        for email in emails_results_msgs :
            msgs.add(email['id'])        
        msgs_to_save_list = list(msgs)
        emails_to_write = set()
        print(f"Fetched {len(msgs_to_save_list)} emails for {label}.Now cleaning.This will take some time")
        for msgid in msgs_to_save_list:
            msg = get_message_from_id(gmail_service,msgid)
            if msg :
                emails_from_dict = email_ids_from_dict(msg)
                emails_to_write.update(emails_from_dict)
            time.sleep(0.5)
        print(f"Completed cleaning.\nNow saving {len(emails_to_write)} email ids of {label}")
        post_processing(emails_to_write,GMAIL_SHEET_INFO['sheet_url'],GMAIL_SHEET_INFO['email_ids_worksheet'])    
        print(f"Saved {len(emails_to_write)} of {label}")
        email_res_keys = list(emails_results.keys())

        nextpage = False
        for key in email_res_keys:
            if key=='nextPageToken':
                nextpage=True
                break
        if nextpage :
            try :
                if query :
                    emails_results = gmail_service.users().messages().list(userId=GMAIL_USER_ID,labelIds=[label],q=query,maxResults=GMAIL_MAX_RESULTS,pageToken=emails_results['nextPageToken']).execute()     
                else:                
                    emails_results = gmail_service.users().messages().list(userId=GMAIL_USER_ID,labelIds=[label],maxResults=GMAIL_MAX_RESULTS,pageToken=emails_results['nextPageToken']).execute()
                emails_results_msgs = emails_results.get('messages',[])
                print(f"{len(emails_results_msgs)} more emails found in {label}")
            except Exception as e :
                error_message = f"Error occured in getting emails of label - {e}"
                print(error_message)
        else :
            break

def get_email_ids(gmail_service,label,query=None):
    get_all_required_emails_messages(gmail_service,label,query) 

def get_all_emails_from_gmail_acct(gmail_service):
    print(f"Fetching all the labels")
    all_labels = get_labels(gmail_service)
    print("All labels fetched")
    # all_labels = GMAIL_LABELS_LIST
    for label in all_labels:
        print(f"Processing for {label}")
        get_email_ids(gmail_service,label)
        print(f"Done with {label}")


def get_email_ids_from_last_run():
    gmail_service = setup_gmail_api()
 
    # Get row column of email id of user
    row_col_of_user_gmail_id = find_cell_row_col(GMAIL_USER_ID,GMAIL_SHEET_INFO['sheet_url'],GMAIL_SHEET_INFO['last_run_worksheet'])

    # If the user has already run this script before
    if row_col_of_user_gmail_id is not None : 
        try : 
            row = row_col_of_user_gmail_id[0]
            col = row_col_of_user_gmail_id[1]
            
            # Get last run date from next column
            last_run_date_str = get_val_from_row_col(row,col+1,GMAIL_SHEET_INFO['sheet_url'],GMAIL_SHEET_INFO['last_run_worksheet'])
        
            # The API call has 2 query string parameters after and before which takes dates (Refer the API call)
            # Here the after is included and before is not [after,before)
            # So last_run_date_str = after and tomorrow_date = before so that emails of today are also included
            
            today_date = datetime.datetime.now()
            tomorrow_date_str = str(datetime.timedelta(days=1) + today_date)  
            tomorrow_date_str = extract_date(tomorrow_date_str)
            
            for email_type in GMAIL_EMAIL_TYPES:
                # Date format in query string = YYYY/MM/DD 
                query_string = f"in:{email_type} after:{last_run_date_str} before:{tomorrow_date_str}"
                get_email_ids(gmail_service,GMAIL_LABELS[email_type],query_string)            
            today_date = str(datetime.datetime.now())
            date_to_write = extract_date(today_date)
            update_date_in_sheet(date_to_write,row,col+1)                                              
        except Exception as e :
            print(f"Error occured in last run - {e}")
    else :
        try :
            get_all_emails_from_gmail_acct(gmail_service)
            today_date = str(datetime.datetime.now())
            date_to_write = extract_date(today_date)
            rows_to_write = [[GMAIL_USER_ID,date_to_write]]
            append_to_sheet(rows_to_write,GMAIL_SHEET_INFO['sheet_url'],GMAIL_SHEET_INFO['last_run_worksheet'])
        except Exception as e : 
            print(f"Error occured in all emails from gmail acct - {e}")
            

def delete_all_emails_of_specific_gmail_id():
    gmail_service = setup_gmail_api()
    # TO DO -> Try to take this following target_id as input
    target_id = GMAIL_TARGET_ID
    query = f"from:{target_id}"
    msg_ids_from_target = []
    all_labels=get_labels(gmail_service)

    for label in all_labels:
        msg_ids_for_label = get_all_required_emails_messages(gmail_service,label,query)
        msg_ids_from_target.extend(msg_ids_for_label)
    unique_msg_ids = list(set(msg_ids_from_target))
    
    if len(unique_msg_ids)==0:
        print(f"No emails found from {target_id}")
        return

    try:
        res = gmail_service.users().messages().batchDelete(userId=GMAIL_USER_ID,body={'ids':unique_msg_ids}).execute()
        print(f"Deleted {len(unique_msg_ids)} successfully")
    except Exception as e: 
        error_msg=f"Error occured while deleting emails from specific id - {e}"
        print(error_msg)


def extract_body_from_mail(message):
    payload = message['payload']
    parts = payload['parts']
    text=""
    for part in parts : 
        if part['mimeType']=="text/plain":
            body_text= part['body']['data']
            decoded_text = decode_base_64_string(body_text)
            decoded_text=decoded_text.decode()  # Convert bytes to string
            text+=decoded_text
    return text

def get_all_messages_body_from_specific_gmail_id():
    gmail_service = setup_gmail_api()
    target_id = GMAIL_TARGET_ID
    query = f"from:{target_id}"
    messages_ids_from_target_id = get_all_required_emails_messages(gmail_service,GMAIL_LABELS['inbox'],query)

    if len(messages_ids_from_target_id)==0:        
        print(f"No emails found from {target_id}")
        return

    for msg_id in messages_ids_from_target_id :
        msg = get_message_from_id(gmail_service,msg_id)
        bodytext = extract_body_from_mail(msg)
        new_data = [[target_id,bodytext]]
        append_to_sheet(new_data,GMAIL_SHEET_INFO['sheet_url'],GMAIL_SHEET_INFO['email_body_worksheet'])        



get_email_ids_from_last_run()
# delete_all_emails_of_specific_gmail_id()
# get_all_messages_body_from_specific_gmail_id()


