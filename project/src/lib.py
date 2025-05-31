from enum import Enum
from datetime import date, datetime, timedelta

class Meridiem(Enum):
    AM = 0
    PM = 12

class Weekday(Enum):
    def __new__(cls, value, label):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.label = label
        return obj

    MON = (1, "Monday")
    TUE = (2, "Tuesday")
    WED = (3, "Wednesday")
    THU = (4, "Thursday")
    FRI = (5, "Friday")
    SAT = (6, "Saturday")
    SUN = (7, "Sunday")

class Month(Enum):
    def __new__(cls, value, label):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.label = label
        return obj

    JAN = (1, "January")
    FEB = (2, "February")
    MAR = (3, "March")
    APR = (4, "April")
    MAY = (5, "May")
    JUN = (6, "June")
    JUL = (7, "July")
    AUG = (8, "August")
    SEP = (9, "September")
    OCT = (10, "October")
    NOV = (11, "November")
    DEC = (12, "December")

class Date:
    def __init__(self,
        day:int,
        month:Month,
        year:int
    ):
        try:
            temp = date(year, month.value, day)
        except:
            raise ValueError(f"ERROR: Invalid Date {day}/{month.label}/{year}")

        self.day = day
        self.month = month
        self.year = year
        self.weekday = Weekday(temp.weekday() + 1)

    def date_to_date(self) -> date:
        return date(self.year, self.month.value, self.day)

    def __lt__(self, other):
        if isinstance(other, Date):
            return self.date_to_date() < other.date_to_date()
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Date):
            return self.date_to_date() <= other.date_to_date()
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Date):
            return self.date_to_date() == other.date_to_date()
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Date):
            return self.date_to_date() != other.date_to_date()
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Date):
            return self.date_to_date() > other.date_to_date()
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Date):
            return self.date_to_date() >= other.date_to_date()
        return NotImplemented

    def __hash__(self):
        return hash((self.day, self.month.value, self.year))

    def __str__(self):
        return f"{self.weekday.label} {self.day}/{self.month.label}/{self.year}"

def date_to_date(date:date) -> Date:
    return Date(date.day, Month(date.month), date.year)

def string_to_date(string:str) -> Date:

    DEFAULT_YEAR = 2025

    temp = string.split("/")
    day = int(temp[1])
    month = Month(int(temp[0]))
    year = int(temp[2])
    return Date(day,month,DEFAULT_YEAR)

class DateRange:
    def __init__(self,
        start:Date,
        end:Date
    ):
        if not (start <= end):
            raise ValueError(f"ERROR: Invalid DateRange {start} ~ {end}")

        self.start = start
        self.end = end

    def within_range(self, day:Date) -> bool:
        return self.start <= day <= self.end

    def to_date_list(self) -> list[Date]:
        temp = []
        current = self.start.date_to_date()

        while current <= self.end.date_to_date():
            temp.append(date_to_date(current))
            current += timedelta(days=1)

        return temp

    def week_day_display(self):
        return f"{self.start.weekday.label} {self.start.day} - {self.end.weekday.label} {self.end.day}"

    def month_day_number_display(self):
        return f"{self.start.month.label} {self.start.day} - {self.end.month.label} {self.end.day}"

    def __str__(self):
        return f"{self.start} - {self.end}"

class Time:

    def __init__(self,
        hour:int,
        minute:int,
        meridiem:Meridiem
    ):

        if not (1 <= hour <= 12):
            raise ValueError(f"ERROR: Invalid Hour {hour}")

        if not (0 <= minute <= 59):
            raise ValueError(f"ERROR: Invalid Minute {minute}")

        self.hour = hour
        self.minute = minute
        self.second = 0
        self.meridiem = meridiem

    def __eq__(self, other):
        return (
            self.hour == other.hour and
            self.minute == other.minute and
            self.second == other.second and
            self.meridiem == other.meridiem
        )

    def __gt__(self, other):
        return (
            (self.meridiem.value * 60 * 60 + (self.hour % 12) * 60 + self.minute, self.second)
            >
            (other.meridiem.value * 60 * 60 + (other.hour % 12) * 60 + other.minute, other.second)
        )

    def to_minutes(self) -> int:
        minutes = self.hour % 12 + self.meridiem.value
        minutes *= 60
        minutes += self.minute
        return minutes

    def __hash__(self):
        return hash((self.hour, self.minute, self.second, self.meridiem.value))

    def __str__(self):
        return f"{self.hour}:{self.minute:02} {self.meridiem.name.upper()}"

# TODO: Specific Time Dictionary

def string_to_time(string:str) -> Time:

    if string == "Open":
        return Time(2,22,Meridiem.AM)

    if string == "Close":
        return Time(11,11,Meridiem.PM)

    temp = string.split(":")

    hour = int(temp[0])
    minute = int(temp[1][:2])
    meridian = Meridiem.AM if temp[1][2:] == "am" else Meridiem.PM

    return Time(hour,minute,meridian)

class TimeRange:

    def __init__(self,
        start:Time,
        end:Time
    ):
        if not (start.to_minutes() <= end.to_minutes()):
            raise ValueError(f"ERROR: Invalid TimeRange {start} ~ {end}")

        self.start = start
        self.end = end

    def __str__(self):

        # ! Special Cases:
        # * 4:04 AM -> NA (both)
        # * 2:22 AM -> Open
        # * 11:11 PM -> Close

        if self.start == Time(1,1,Meridiem.AM) and self.end == Time(1,1,Meridiem.AM):
            return "ERROR"

        if self.start == Time(4,4,Meridiem.AM) and self.end == Time(4,4,Meridiem.AM):
            return "NA"

        if self.start == Time(2,22,Meridiem.AM) and self.end == Time(11,11,Meridiem.PM):
            return "All Day"

        if self.start == Time(2,22,Meridiem.AM):
            return f"Open - {self.end}"

        if self.end == Time(11,11,Meridiem.PM):
            return f"{self.start} - Close"

        return f"{self.start} - {self.end}"

def convert_time(string:str) -> TimeRange:

    match string:

        case "NA":
            return TimeRange(Time(4,4,Meridiem.AM),Time(4,4,Meridiem.AM))

        case "Open":
            return TimeRange(Time(2,22,Meridiem.AM),Time(4,0,Meridiem.PM))

        case "Close":
            return TimeRange(Time(2,0,Meridiem.PM),Time(11,11,Meridiem.PM))

        case "All Day":
            return TimeRange(Time(2,22,Meridiem.AM),Time(11,11,Meridiem.PM))

        case _:
            return TimeRange(Time(1,1,Meridiem.AM),Time(1,1,Meridiem.AM))

def custom_time(string:str) -> TimeRange:
    string = "".join(string.split())
    mid = string.split("-")
    start = Time(2,22,Meridiem.AM) if mid[0] == "Open" else string_to_time(mid[0])
    end = Time(11,11,Meridiem.PM) if mid[1] == "Close" else string_to_time(mid[1])
    return TimeRange(start,end)

def string_to_Date_Time(string:str) -> tuple[Date,Time]:

    date_part, time_part = string.strip().split(" ")

    temp_date = string_to_date(date_part)

    hour, minute, second = map(int, time_part.split(":"))
    meridiem = Meridiem.AM if hour < 12 else Meridiem.PM
    hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12

    temp_time = Time(hour, minute, meridiem)
    temp_time.second = second

    return temp_date, temp_time
