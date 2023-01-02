import time
from gmail_constants import *  
from utils import *
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
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

def get_email_ids_from_email_dict(email_dict,email_ids):
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

def get_email_ids(gmail_service,label,email_ids_set,query=None):
    before_len = len(email_ids_set)
    try :
        if query :
            emails_results = gmail_service.users().messages().list(userId=GMAIL_USER_ID,labelIds=[label],q=query,maxResults=GMAIL_MAX_RESULTS).execute()
        else:
            emails_results = gmail_service.users().messages().list(userId=GMAIL_USER_ID,labelIds=[label],maxResults=GMAIL_MAX_RESULTS).execute()
        emails_results_msgs = emails_results.get('messages',[])
        print(f"{len(emails_results_msgs)} emails found in {label}")
    except Exception as e :
        error_message = f"Error occured in getting emails of label - {e}"
        print(error_message)
        return None
    
    while True:
        for email in emails_results_msgs :
            msg = None
            try :
                msg = gmail_service.users().messages().get(userId=GMAIL_USER_ID,id=email['id']).execute()
            except Exception as e:
                error_message = f"Error occured while fetching email with id {email['id']} - {e}"
                print(error_message)
                continue
            get_email_ids_from_email_dict(msg,email_ids_set)
        
        if 'nextPageToken' in emails_results :
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

def get_all_emails_from_gmail_acct(gmail_service):
    email_ids = set()
    all_labels = get_labels(gmail_service)

    for label in all_labels:
        get_email_ids(gmail_service,label,email_ids)
        
    return email_ids


    
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
            
            email_ids = set()
            for email_type in GMAIL_EMAIL_TYPES:
                # Date format in query string = YYYY/MM/DD 
                query_string = f"in:{email_type} after:{last_run_date_str} before:{tomorrow_date_str}"
                get_email_ids(gmail_service,GMAIL_LABELS[email_type],email_ids,query_string)
            
            today_date = str(datetime.datetime.now())
            date_to_write = extract_date(today_date)
            post_processing(email_ids,GMAIL_SHEET_INFO['sheet_url'],GMAIL_SHEET_INFO['email_ids_worksheet'])
            update_date_in_sheet(date_to_write,row,col+1)                                              
        except Exception as e :
            print(f"Error occured in last run - {e}")
    else :
        try :
            email_ids = get_all_emails_from_gmail_acct(gmail_service)
            post_processing(email_ids,GMAIL_SHEET_INFO['sheet_url'],GMAIL_SHEET_INFO['email_ids_worksheet'])
            today_date = str(datetime.datetime.now())
            date_to_write = extract_date(today_date)
            rows_to_write = [[GMAIL_USER_ID,date_to_write]]
            append_to_sheet(rows_to_write,GMAIL_SHEET_INFO['sheet_url'],GMAIL_SHEET_INFO['last_run_worksheet'])
        except Exception as e : 
            print(f"Error occured in all emails from gmail acct - {e}")
            
get_email_ids_from_last_run()





