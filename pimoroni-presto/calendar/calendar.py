# https://github.com/creativenucleus/rpi-public

import datetime
import math
import time

from presto import Presto

presto = Presto(True)
display = presto.display
WIDTH, HEIGHT = display.get_bounds()

today = datetime.date.today()
YEAR, MONTH = today.year, today.month

class Day:
    def __init__(self, x, y, w, h, text):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text

days = None

# This is a crazy thing to have to do, but *¯\_(ツ)_/¯* Python!
# https://stackoverflow.com/questions/42950/get-the-last-day-of-the-month
def getDaysInMonth(year, month):
    date = datetime.date(year, month, 1)
    # The day 28 exists in every month. 4 days later, it's always next month
    nextMonth = date.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return (nextMonth.replace(day=1) - date).days

def initDays(year, month):
    global days
    days = []
    iDay=datetime.date(year, month, 1).weekday()
    daysInMonth = getDaysInMonth(year, month)
    for i in range(0, daysInMonth):
        w = 60
        h = 60
        x = 2+68*(iDay%7)+4
        y = 62+68*math.floor(iDay/7)
        days.append(Day(int(x),int(y),int(w),int(h),str(i+1)))
        iDay=iDay+1

PEN_BG = display.create_pen(20, 0, 60)
PEN_DAY_BG = display.create_pen(255, 255, 255)
PEN_DAY_NUMBER = display.create_pen(60, 150, 255)

initDays(YEAR, MONTH)

touch = presto.touch
updateScreen = True

while True:
    touch.poll()
    if touch.state:
        if touch.x<240:
            MONTH = MONTH - 1
            if MONTH < 1:
                MONTH = 12
                YEAR = YEAR - 1
        else:
            MONTH = MONTH + 1
            if MONTH > 12:
                MONTH = 1
                YEAR = YEAR + 1
        initDays(YEAR, MONTH)
        updateScreen = True

    if updateScreen:
        display.set_layer(0)
        display.set_pen(PEN_BG)
        display.clear()

        display.set_pen(PEN_DAY_NUMBER)
        monthNames = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        text = f"{monthNames[MONTH-1]} {str(YEAR)}"
        textW = display.measure_text(text, 3)
        display.text(text, int(240-textW/2), 6, textW, 3)

        dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, dayName in enumerate(dayNames):
            display.text(dayName, 16 + i*68, 38)
            
        for day in days:
            display.set_pen(PEN_DAY_BG)
            display.rectangle(day.x, day.y, day.w, day.h)
            
            display.set_pen(PEN_DAY_NUMBER)
            display.text(day.text, day.x+4, day.y+4)

        presto.update()
        updateScreen = False
    
    time.sleep(1/15)
