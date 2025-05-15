from enum import Enum
from datetime import date

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

# TODO: Make a date string -> date

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

    def __str__(self):
        return f"{self.weekday.label} {self.day}/{self.month.label}/{self.year}"

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
        self.meridiem = meridiem

    def to_minutes(self) -> int:
        minutes = self.hour % 12 + self.meridiem.value
        minutes *= 60
        minutes += self.minute
        return minutes

    def __str__(self):
        return f"{self.hour}:{self.minute:02}{self.meridiem.name.lower()}"

class TimeRange:
    def __init__(self,
        start:Time,
        end:Time
    ):
        if not (start.to_minutes() < end.to_minutes()):
            raise ValueError(f"ERROR: Invalid TimeRange {start} ~ {end}")

        self.start = start
        self.end = end

    def __str__(self):
        return f"{self.start} - {self.end}"

class Employee:
    def __init__(self,
        email:str,
        name:str,
        phone:str,
        weekly_availability:list[TimeRange],
        weekly_shifts_prefs:tuple[int,int]
    ):
        self.email = email
        self.name = name
        self.phone = phone
        self.weekly_availability = weekly_availability
        self.weekly_shifts_prefs = weekly_shifts_prefs
