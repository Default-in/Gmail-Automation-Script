# Gmail-Automation-Script

This script will fetch all email ids of interactions done by a gmail account (To,From,Cc,Bcc everyone in the conversation)

Since this is a standalone script it will be easy to setup on your machine.

Follow this steps to setup it on your machine.

1. Clone this repo
2. Delete token.json and gmail_credentials.json
3. Create your credentials on Google Cloud Console for OAuth Client.
   Follow the below mentioned steps to generate Credentials

   ***

   1. Go to google cloud console and open the menu from top left corner.
   2. Go to API and Services (In Enabled API's and Services you will be able to see the active APIs and monitor them)
   3. Click on Credentials from the list
   4. After this click on create credentials and click OAuth Client ID
   5. It will ask for application type,you can provide the application type on which you are working (Web,Desktop etc)
   6. Click on create and your credentials will be created.
   7. Now click on "Download JSON" and save it in your repository directory.
   8. Refer the code in Automation Repo sourcing>automations>gmail_actions in setup_gmail_api function to know how to use this credentials to generate token.
   9. After the first time,token.json is created and next time it will refer to this created token only instead of creating new token from credentials.

   ***

4. Make sure you have renamed your credentials as gmail_credentials.json and this file should be in the same directory where the all the files of gmail automation are present.
5. Go to gmail_constants.py and change the constant "GMAIL_USER_ID" = youremail@example.com
6. youremail@example.com is the same email through which credentials are created.
