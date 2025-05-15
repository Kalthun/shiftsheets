# imports
from flask import Flask, request
from google.oauth2 import service_account
from googleapiclient.discovery import build

import pandas as pd
from tabulate import tabulate

import pathlib
import lib

# ================ #

BASE_PATH = pathlib.Path.cwd().resolve()
SERVICE_ACCOUNT_PATH = BASE_PATH / "project" / "keys" / "service-account-key.json"
SECRET_TOKEN_PATH = BASE_PATH / "project" / "keys" / "secret-token.txt"

# ================ #

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH)
service = build("sheets", "v4", credentials=credentials)

# ================ #

SHEET_ID = "1vID-hTj_GR0XUpynUm1BnLNL28BTV2JHxe_a2LIssAw"

WA_PAGE = "WA"
AA_PAGE = "AA"

WEEKS = {
    "May 26 - June 8" : lib.DateRange(lib.Date(26, lib.Month.MAY, 2025), lib.Date(8, lib.Month.JUN, 2025)),
    "June 9 - June 22" : lib.DateRange(lib.Date(9, lib.Month.JUN, 2025), lib.Date(22, lib.Month.JUN, 2025)),
    "June 23 - July 6" : lib.DateRange(lib.Date(23, lib.Month.JUN, 2025), lib.Date(6, lib.Month.JUL, 2025)),
    "July 7 - July 20" : lib.DateRange(lib.Date(7, lib.Month.JUL, 2025), lib.Date(20, lib.Month.JUL, 2025)),
    "July 21 - Aug 3" : lib.DateRange(lib.Date(21, lib.Month.JUL, 2025), lib.Date(3, lib.Month.AUG, 2025)),
    "Aug 4 - Aug 17" : lib.DateRange(lib.Date(4, lib.Month.AUG, 2025), lib.Date(17, lib.Month.AUG, 2025)),
    "Aug 18 - Aug 31" : lib.DateRange(lib.Date(18, lib.Month.AUG, 2025), lib.Date(31, lib.Month.AUG, 2025)),
    "Sept 1 - Sept 14" : lib.DateRange(lib.Date(1, lib.Month.SEP, 2025), lib.Date(14, lib.Month.SEP, 2025)),
    "Sept 15 - Sept 28" : lib.DateRange(lib.Date(15, lib.Month.SEP, 2025), lib.Date(28, lib.Month.SEP, 2025)),
    "Sept 29 - Oct 12" : lib.DateRange(lib.Date(29, lib.Month.SEP, 2025), lib.Date(12, lib.Month.OCT, 2025)),
    "Oct 13 - Oct 26" : lib.DateRange(lib.Date(13, lib.Month.OCT, 2025), lib.Date(26, lib.Month.OCT, 2025))
}

for week in WEEKS:
    print(week)

# TODO: Consider Helpers for getting WA and AA

# ================ #

sheet_data = service.spreadsheets().values().get(
    spreadsheetId = SHEET_ID,
    range = WA_PAGE
).execute()

raw_values = sheet_data.get("values", [])

WA_data = pd.DataFrame(raw_values[1:], columns=raw_values[0])

print(tabulate(WA_data, headers='keys', tablefmt='fancy_grid', showindex=False))

# ================ #

sheet_data = service.spreadsheets().values().get(
    spreadsheetId = SHEET_ID,
    range = AA_PAGE
).execute()

raw_values = sheet_data.get("values", [])

AA_data = pd.DataFrame(raw_values[1:], columns=raw_values[0])

print(tabulate(AA_data, headers='keys', tablefmt='fancy_grid', showindex=False))

# ================ #

# ! Write Code Here

# ================ #

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():

    key = request.headers.get("Authorization")

    if key != open(SECRET_TOKEN_PATH).read().strip():
        return "Forbidden, 403"

    payload = request.data.decode("utf-8")
    if payload.strip().lower() == "ping":

       print("Updating Sheets")

       # * Put New Code Here

    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)
