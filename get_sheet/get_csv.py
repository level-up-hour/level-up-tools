#!/usr/bin/env python3

# largely cribbed from:
# https://github.com/billydh/python-google-drive-api
# https://medium.com/swlh/google-drive-api-with-python-part-i-set-up-credentials-1f729cb0372b
# https://towardsdatascience.com/how-to-download-a-specific-sheet-by-name-from-a-google-spreadsheet-as-a-csv-file-e8c7b4b79f39

import re
import argparse
import csv
from googleapiclient import discovery, errors
from httplib2 import Http
from oauth2client import file, client, tools

def get_api_services():
    # define credentials and client secret file paths
    credentials_file_path = './credentials/credentials.json'
    clientsecret_file_path = './credentials/client_secret.json'

    # define scope
    SCOPE = 'https://www.googleapis.com/auth/drive'

    # define store
    store = file.Storage(credentials_file_path)
    credentials = store.get()

    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(clientsecret_file_path, SCOPE)
        credentials = tools.run_flow(flow, store)

    # define API service
    http = credentials.authorize(Http())
    drive = discovery.build('drive', 'v3', http=http)
    sheets = discovery.build('sheets', 'v4', credentials=credentials)

    return drive, sheets

def get_spreadsheet_id(api_service, spreadsheet_name):
    results = []
    page_token = None

    while True:
        try:
            param = {'q': 'mimeType="application/vnd.google-apps.spreadsheet"'}

            if page_token:
                param['pageToken'] = page_token

            files = api_service.files().list(**param).execute()
            results.extend(files.get('files'))

            # Google Drive API shows our files in multiple pages when the number of files exceed 100
            page_token = files.get('nextPageToken')

            if not page_token:
                break

        except errors.HttpError as error:
            print(f'An error has occurred: {error}')
            break

    spreadsheet_id = [result.get('id') for result in results if result.get('name') == spreadsheet_name][0]

    return spreadsheet_id

def download_sheet_to_csv(sheets_instance, spreadsheet_id, sheet_name):
    result = sheets_instance.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
    fn = re.sub(r"[^A-Za-z0-9]", "-", sheet_name).strip() + '.csv'

    with open(fn, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(result.get('values'))

    f.close()

    print("{} sheet downloaded to '{}'".format(sheet_name, fn))

def parse_args():
    parser = argparse.ArgumentParser(description="""
    Function to download a specific sheet from a Google Spreadsheet.
    You must provide a spreadsheet-name or spreadsheet-id. You must also
    have credentials stored in the credentials folder to access the Google Sheets API.
    Please see instructions here: https://medium.com/swlh/google-drive-api-with-python-part-i-set-up-credentials-1f729cb0372b
    """)

    parser.add_argument("--spreadsheet-name", required=False, help="The name of the Google Sheet (searching by name is slow)")
    parser.add_argument("--spreadsheet-id", required=False, help="The id of the Google Spreadsheet")
    parser.add_argument("--sheet-name", required=True, help="The name of the sheet in the spreadsheet to download as csv")

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    drive, sheets = get_api_services()
    if args.spreadsheet_id == None:
        args.spreadsheet_id = get_spreadsheet_id(drive, args.spreadsheet_name)
        print("Spreadsheet ID is {}. We recommend that you use that flag next time for better performance.".format(args.spreadsheet_id))
    download_sheet_to_csv(sheets, args.spreadsheet_id, args.sheet_name)
