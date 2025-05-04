from google.oauth2 import service_account
from googleapiclient.discovery import build

import pandas as pd
from tabulate import tabulate

import pathlib

BASE_PATH = pathlib.Path.cwd().resolve()
SERVICE_ACCOUNT_FILE = BASE_PATH / "project" / "keys" / "service-account-key.json"

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
service = build("sheets", "v4", credentials=credentials)

SHEET_ID = "1vID-hTj_GR0XUpynUm1BnLNL28BTV2JHxe_a2LIssAw"
WA_PAGE = "WA"
AA_PAGE = "AA"
TEMPLATE_PAGE = "TEMPLATE"

sheet_data = service.spreadsheets().values().get(
    spreadsheetId = SHEET_ID,
    range = WA_PAGE
).execute()

raw_values = sheet_data.get("values", [])

data = pd.DataFrame(raw_values[1:], columns=raw_values[0])

print(tabulate(data, headers='keys', tablefmt='fancy_grid', showindex=False))
