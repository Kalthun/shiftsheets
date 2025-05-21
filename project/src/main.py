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
TEMPLATE_ID = "T25-V1"

# ================ #

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

# B1 : Month Day - Month Day

# B -> Phone
# C -> Name
# D -> Prefs

# E1 - K1 : week 1
# M1 - S1 : week 2

# Col A for email linking

# Row index by email

# ================ #

def get_page_names(sheet_id:str) -> list[str]:
    response = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheets = response.get("sheets", [])
    return [sheet["properties"]["title"] for sheet in sheets]

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
        preferences:str # ! see commit "here we are" for tuple
    ):
        self.email = email.strip()
        self.name = name.strip()
        self.phone = phone.strip()
        self.weekly_availability = weekly_availability
        self.preferences = preferences.strip()

    def __str__(self):
        availability = "\n".join(
            f"{day}: {str(time_range)}"
            for day, time_range in self.weekly_availability.items()
        )
        return f"{self.email}: {self.name} | {self.phone} | {self.preferences}\n{availability}"

# ================ #

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
            # TODO: Consider wrapping in function
            if custom != "":
                custom = "".join(custom.split())
                days = custom.split(",")
                for day in days:
                    if day != "":
                        # TODO: At least this part
                        temp = day.split(":",1)
                        weekday = temp[0].lower()
                        time_range = temp[1]
                        mid = time_range.split("-")
                        start = lib.Time(2,22,lib.Meridiem.AM) if mid[0] == "Open" else lib.string_to_time(mid[0])
                        end = lib.Time(11,11,lib.Meridiem.PM) if mid[1] == "Close" else lib.string_to_time(mid[1])
                        weekly_availability[weekday] = lib.TimeRange(start,end)

        temp = worker[WA_KEY_MAP["preferences"]].split(",")
        preferences = temp[0] if len(temp) < 2 else f"{temp[0].strip()}-{temp[1].strip()}"

        workers.append(Worker(
            email=worker[WA_KEY_MAP["email"]],
            name=worker[WA_KEY_MAP["name"]],
            phone=worker[WA_KEY_MAP["phone"]],
            weekly_availability=weekly_availability,
            preferences=preferences
        ))

    return workers

# ================ #

# TODO: use in get worker instead
def get_indexs(sheet:str, page:str, emails:list[str]) -> dict[str,int]:

    entries = service.spreadsheets().values().get(
        spreadsheetId=sheet,
        range=f"{page}!A1:A78"
    ).execute().get("values", [])

    entries = [row[0] if row else "" for row in entries]
    temp:dict[str,int] = {}

    for email in emails:
        temp[email] = entries.index(email) + 1

    return temp

# ================ #

def fill_row(page:str, worker:Worker):
    pass

# ================ #

def update():

    # today = lib.date_to_date(lib.datetime.today())
    # print(today)

    WA_data = get_page(WA_PAGE)

    workers = get_workers(WA_data)

    for worker in workers:
        print(worker)
        print()

    for key,value in get_indexs(SHEET_ID, TEMPLATE_ID, [worker.email for worker in workers]).items():
        print(f"{key}:{value}")

    # TODO: Do this in get workers as well
    AA_data = get_page(AA_PAGE)
    # for _,row in AA_data.iterrows():
    #     # * 1: check time-range to current sheet
    #     # * 2:
    #     pass

    weeks = list(WEEKS.keys()) # * Only fill weeks that exist
    pages = get_page_names(SHEET_ID)
    active_periods = list(set(weeks) & set(pages))

    for biweek in active_periods:
        for worker in workers:
            fill_row(biweek,worker)

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
