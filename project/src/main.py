# from flask import Flask, request
from google.oauth2 import service_account
from googleapiclient.discovery import build

import pandas as pd
from tabulate import tabulate

import pathlib
import lib

# ================ #

BASE_PATH = pathlib.Path.cwd().resolve()
SERVICE_ACCOUNT_PATH = BASE_PATH / "project" / "keys" / "service-account-key.json"
# SECRET_TOKEN_PATH = BASE_PATH / "project" / "keys" / "secret-token.txt"
ERROR_PATH = BASE_PATH / "project" / "outputs" / "errors.txt"

# ================ #

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH)
service = build("sheets", "v4", credentials=credentials)

# ================ #

SHEET_ID = "1vID-hTj_GR0XUpynUm1BnLNL28BTV2JHxe_a2LIssAw"

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

# TODO: Get rid of old AA entries
def remove_old():
    pass

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

def display_page(page:pd.DataFrame):
    print(tabulate(get_page(page), headers="keys", tablefmt="fancy_grid", showindex=False))

# ================ #

class Worker:

    def __init__(self,
        email:str,
        name:str,
        phone:str,
        availability:dict[str,lib.TimeRange],
        alternate:list[tuple[lib.Date,lib.TimeRange,tuple[lib.Date,lib.Time]]],
        preferences:tuple[int,int]
    ):
        self.email = email.strip()
        self.name = name.strip()
        self.phone = phone.strip()
        self.availability = availability
        self.alternate = alternate
        self.preferences = preferences

    def __str__(self):

        availability = "\n".join(
            f"{day}: {str(time_range)}"
            for day, time_range in self.availability.items()
        )

        alternate_table = [
            [str(date), str(time_range), f"{timestamp[0]} {timestamp[1]}"]
            for date, time_range, timestamp in self.alternate
        ]

        alternate = tabulate(
            alternate_table,
            headers=["Date", "Time Range", "Submitted At"],
            tablefmt="grid"
        )

        preferences = f"{self.preferences[0]}" if self.preferences[0] == self.preferences[1] else f"{self.preferences[0]}-{self.preferences[1]}"

        return f"{self.email}: {self.name} | {self.phone} | {preferences}\n\n{availability}\n\n{alternate}"

# ================ #

def clean_AA(data:list[tuple[lib.Date,lib.TimeRange,tuple[lib.Date,lib.Time]]]) -> list[tuple[lib.Date,lib.TimeRange,tuple[lib.Date,lib.Time]]]:

    latest_map: dict[lib.Date, tuple[lib.TimeRange, tuple[lib.Date, lib.Time]]] = {}

    for date_of, time_range, timestamp in data:
        if date_of not in latest_map:
            latest_map[date_of] = (time_range, timestamp)
        else:
            _, existing_timestamp = latest_map[date_of]
            if timestamp > existing_timestamp:  # your Date + Time comparison works directly
                latest_map[date_of] = (time_range, timestamp)

    return [(date, time_range, timestamp) for date, (time_range, timestamp) in latest_map.items()]

# ================ #

def get_workers(data:pd.DataFrame) -> list[Worker]:

    workers:list[Worker] = []

    AA_data = get_page(AA_PAGE)

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

        # TODO: Add custom in the convert_time step
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
                        weekly_availability[weekday] = lib.custom_time(time_range)

        alternate_availability: list[tuple[lib.Date, lib.TimeRange, tuple[lib.Date, lib.Time]]] = []

        for _,entry in AA_data[AA_data[AA_KEY_MAP["email"]] == worker[WA_KEY_MAP["email"]]].iterrows():

            start = lib.string_to_date(entry[AA_KEY_MAP["start"]])

            if entry[AA_KEY_MAP["end"]] == "":
                if entry[AA_KEY_MAP["new"]] == "Custom":
                    alternate_availability.append((start,lib.custom_time(entry[AA_KEY_MAP["custom"]]),lib.string_to_Date_Time(entry[AA_KEY_MAP["time"]])))
                else:
                    alternate_availability.append((start,lib.convert_time(entry[AA_KEY_MAP["new"]]),lib.string_to_Date_Time(entry[AA_KEY_MAP["time"]])))

            else:
                end = lib.string_to_date(entry[AA_KEY_MAP["end"]])

                # TODO: Make seperate function
                if end < start:
                    timestamp = lib.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(ERROR_PATH, "a") as f:
                        f.write(f"[{timestamp}] Invalid date range: {start} to {end} for {worker[WA_KEY_MAP['name']]} <{worker[WA_KEY_MAP['email']]}>.\n\n")
                    continue

                date_range = lib.DateRange(start,end)
                days = date_range.to_date_list()

                for day in days:
                    if entry[AA_KEY_MAP["new"]] == "Custom":
                        alternate_availability.append((day,lib.custom_time(entry[AA_KEY_MAP["custom"]]),lib.string_to_Date_Time(entry[AA_KEY_MAP["time"]])))
                    else:
                        alternate_availability.append((day,lib.convert_time(entry[AA_KEY_MAP["new"]]),lib.string_to_Date_Time(entry[AA_KEY_MAP["time"]])))

        alternate_availability = clean_AA(alternate_availability)
        alternate_availability.sort(key=lambda x: x[0])

        temp = worker[WA_KEY_MAP["preferences"]].split(",")
        preferences = (int(temp[0]),int(temp[0])) if len(temp) < 2 else (int(temp[0]),int(temp[1]))

        workers.append(Worker(
            email=worker[WA_KEY_MAP["email"]],
            name=worker[WA_KEY_MAP["name"]], # TODO: Fix Case
            phone=worker[WA_KEY_MAP["phone"]],
            availability=weekly_availability,
            alternate=alternate_availability,
            preferences=preferences
        ))

    return workers

# ================ #

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

def fill_page(sheet: str, page:str, workers:list[Worker]):

    weeks = WEEKS[page]

    week_days:list[lib.Date] = weeks.to_date_list()
    week1:list[lib.Date] = week_days[:7]
    week2:list[lib.Date] = week_days[7:14]

    indexes = get_indexs(sheet, page, [worker.email for worker in workers])

    for worker in workers:

        prefs = (
            f"{worker.preferences[0]}"
            if worker.preferences[0] == worker.preferences[1]
            else f"{worker.preferences[0]}-{worker.preferences[1]}"
        )

        week1_values = []
        for date in week1:
            override = next((t for d, t, _ in worker.alternate if d == date), None)
            default = worker.availability[date.weekday.label.lower()]
            week1_values.append(str(override if override else default))

        week2_values = []
        for date in week2:
            override = next((t for d, t, _ in worker.alternate if d == date), None)
            default = worker.availability[date.weekday.label.lower()]
            week2_values.append(str(override if override else default))

        input = [worker.phone, worker.name, prefs] + week1_values + [""] + week2_values

        service.spreadsheets().values().update(
            spreadsheetId=sheet,
            range=f"{page}!B{indexes[worker.email]}:S{indexes[worker.email]}",
            valueInputOption="RAW",
            body={"values": [input]}
        ).execute()

# ================ #

# app = Flask(__name__)

# @app.route("/webhook", methods=["POST"])
# def webhook():

#     key = request.headers.get("Authorization")

#     if key != open(SECRET_TOKEN_PATH).read().strip():
#         return "Forbidden, 403"

#     payload = request.data.decode("utf-8")
#     if payload.strip().lower() == "ping":

#         update()

#     else:
#         return "Unrecognized payload", 400

#     return "OK", 200

# if __name__ == "__main__":
#     app.run(port=5000)

# ================ #

current_week = "June 9 - June 22"

WA_data = get_page(WA_PAGE)
workers = get_workers(WA_data)

for worker in workers:
    if worker.email == "drewrome07@gmail.com":
        print(worker)

fill_page(SHEET_ID, current_week, workers)
