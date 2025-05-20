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

WA_KEY_MAP = {
    "time": "Timestamp",
    "email": "Email Address",
    "name": "What is your first & last name?",
    "phone": "What is your phone number?",
    "monday": "What is your weekly availability? [Monday]",
    "tuesday": "What is your weekly availability? [Tuesday]",
    "wednesday": "What is your weekly availability? [Wednesday]",
    "thursday": "What is your weekly availability? [Thursday]",
    "friday": "What is your weekly availability? [Friday]",
    "saturday": "What is your weekly availability? [Saturday]",
    "sunday": "What is your weekly availability? [Sunday]",
    "custom": "Custom Availability",
    "preferences": "How many shifts would you prefer each week? "
}

AA_PAGE = "AA"

AA_KEY_MAP = {

}

# TODO: used as keys for the spreadsheet

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

TEST_PAGE = "T-25-V1"

# ? NOTES:
# B1 : Month Day - Month Day
# D1 - J1 : week 1
# L1 - R1 : week 2
# Col A for email linking
# Row index by email

# ================ #

def get_page(name:str) -> pd.DataFrame:

    temp = service.spreadsheets().values().get(
        spreadsheetId = SHEET_ID,
        range = name
    ).execute().get("values", [])

    return pd.DataFrame(temp[1:], columns=temp[0])

def display_page(page):

    print(tabulate(get_page(page), headers="keys", tablefmt="fancy_grid", showindex=False))

# ================ #

class Worker:

    def __init__(self,
        email:str,
        name:str,
        phone:str,
        weekly_availability:list[lib.TimeRange],
        # weekly_shifts_prefs:tuple[int,int]
    ):
        self.email = email
        self.name = name
        self.phone = phone
        self.weekly_availability = weekly_availability
        # self.weekly_shifts_prefs = weekly_shifts_prefs

    def __str__(self):
        availability_str = "\n".join(str(x) for x in self.weekly_availability)
        return f"{self.email}: {self.name} | {self.phone}\n{availability_str}"

def get_workers(data:pd.DataFrame) -> list[Worker]:

    workers:list[Worker] = []

    weekdays = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday"
        ]

    for _,worker in data.iterrows():

        weekly_availability:list[lib.TimeRange] = []

        # TODO: Make this a function

        for weekday in weekdays:
            match worker[WA_KEY_MAP[weekday]]:
                case "NA":
                    weekly_availability.append(lib.TimeRange(lib.Time(4,4,lib.Meridiem.AM),lib.Time(4,4,lib.Meridiem.AM)))
                case "Open":
                    weekly_availability.append(lib.TimeRange(lib.Time(2,22,lib.Meridiem.AM),lib.Time(4,0,lib.Meridiem.PM)))
                case "Close":
                    weekly_availability.append(lib.TimeRange(lib.Time(2,0,lib.Meridiem.PM),lib.Time(11,11,lib.Meridiem.PM)))
                case "All Day":
                    weekly_availability.append(lib.TimeRange(lib.Time(2,22,lib.Meridiem.AM),lib.Time(11,11,lib.Meridiem.PM)))
                case _:
                    weekly_availability.append(lib.TimeRange(lib.Time(4,4,lib.Meridiem.AM),lib.Time(4,4,lib.Meridiem.AM)))

        # TODO: seperate Custom by , then filter (re-use logic) (also make a function)

        workers.append(Worker(
            email=worker[WA_KEY_MAP["email"]],
            name=worker[WA_KEY_MAP["name"]],
            phone=worker[WA_KEY_MAP["phone"]],
            weekly_availability=weekly_availability
        ))

    for worker in workers:
        print(worker)
        print()

# ================ #

def update():

    WA_data = get_page(WA_PAGE)

    AA_data = get_page(AA_PAGE)

    get_workers(WA_data)

# ================ #

update()

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():

    key = request.headers.get("Authorization")

    if key != open(SECRET_TOKEN_PATH).read().strip():
        return "Forbidden, 403"

    payload = request.data.decode("utf-8")
    if payload.strip().lower() == "ping":

        update()

    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)
