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
    "preferences": "How many shifts would you prefer each week?"
}

# ================ #

AA_PAGE = "AA"

AA_KEY_MAP = {
    "time": "Timestamp",
    "email": "Email Address",
    "start": "What day do you need your availability changed?",
    "end": "What day does your availability go back to normal?",
    "new": "What is your new availability?",
    "custom": "Custom Availability"
}

# ================ #

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

# ================ #

TEST_PAGE = "T25-V1"

# B1 : Month Day - Month Day

# B -> Phone
# C -> Name
# D -> Prefs

# E1 - K1 : week 1
# M1 - S1 : week 2

# Col A for email linking

# Row index by email

# ================ #

def get_page(name:str) -> pd.DataFrame | None:

    temp = service.spreadsheets().values().get(
        spreadsheetId = SHEET_ID,
        range = name
    ).execute().get("values", [])

    if not temp:
        return None

    return pd.DataFrame(temp[1:], columns=temp[0])

def display_page(page):

    print(tabulate(get_page(page), headers="keys", tablefmt="fancy_grid", showindex=False))

# ================ #

class Worker:

    def __init__(self,
        email:str,
        name:str,
        phone:str,
        weekly_availability:dict[str,lib.TimeRange],
        weekly_shifts_prefs:tuple[int,int]
    ):
        self.email = email
        self.name = name
        self.phone = phone
        self.weekly_availability = weekly_availability
        self.weekly_shifts_prefs = weekly_shifts_prefs

    def __str__(self):
        availability = "\n".join(
            f"{day}: {str(time_range)}"
            for day, time_range in self.weekly_availability.items()
        )
        preferences = f"{self.weekly_shifts_prefs[0]}" if self.weekly_shifts_prefs[0] == self.weekly_shifts_prefs[1] else f"{self.weekly_shifts_prefs[0]}-{self.weekly_shifts_prefs[1]}"
        return f"{self.email}: {self.name} | {self.phone} | {preferences}\n{availability}"

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

        weekly_availability:dict[str,lib.TimeRange] = {}

        for weekday in weekdays:
            weekly_availability[weekday] = lib.convert_time(worker[WA_KEY_MAP[weekday]])

        custom_availability = worker[WA_KEY_MAP["custom"]].split(",")

        for custom in custom_availability:
            if custom != "":
                custom = "".join(custom.split())
                days = custom.split(",")
                for day in days:
                    if day != "":
                        temp = day.split(":",1)
                        weekday = temp[0].lower()
                        time_range = temp[1]
                        mid = time_range.split("-")
                        start = lib.Time(2,22,lib.Meridiem.AM) if mid[0] == "Open" else lib.string_to_time(mid[0])
                        end = lib.Time(11,11,lib.Meridiem.PM) if mid[1] == "Close" else lib.string_to_time(mid[1])
                        weekly_availability[weekday] = lib.TimeRange(start,end)

        vals = list(map(int, worker[WA_KEY_MAP["preferences"]].split(",")))
        preferences = tuple(vals if len(vals) == 2 else (vals[0], vals[0]))

        workers.append(Worker(
            email=worker[WA_KEY_MAP["email"]],
            name=worker[WA_KEY_MAP["name"]],
            phone=worker[WA_KEY_MAP["phone"]],
            weekly_availability=weekly_availability,
            weekly_shifts_prefs=preferences
        ))

    return workers

# ================ #

def update():

    WA_data = get_page(WA_PAGE)
    AA_data = get_page(AA_PAGE)

    # today = lib.date_to_date(lib.datetime.today())
    # print(today)

    workers = get_workers(WA_data)

    for worker in workers:
        print(worker)

    for _,row in AA_data.iterrows():
        # * 1: check time-range to current sheet
        # * 2:
        pass

    for key,time_range in WEEKS.items():
        # TODO: Fill in Values
        pass

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

    else:
        return "Unrecognized payload", 400

    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)
