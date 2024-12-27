# https://github.com/creativenucleus/rpi-public

import datetime
import math
import time
import config
import network
import ntptime
import sys
import urequests
import ui

from presto import Presto
from picovector import PicoVector, Polygon

presto = Presto(True)
display = presto.display
vector = PicoVector(display)

BRIGHTNESS = 'regular'
DIM_TIME_IN_S = 30

# use = 'bg', 'day_bg', 'today_bg'
#       'text', 'day_text'
# state = 'regular'|'dim'
PEN_RGBS={
    'bg': (20, 0, 60),
    'text': (255, 255, 255),
    'day_bg': (200, 200, 200),
    'day_bg_today': (255, 255, 128),
    'day_text': (0, 0, 60),
}
def getPen(use, state):
    rgb = PEN_RGBS[use]
    brightness = 1
    if state == 'dim':
        brightness = .2
    return display.create_pen(int(rgb[0] * brightness), int(rgb[1] * brightness), int(rgb[2] * brightness))

# Show startup screen (otherwise we get pixelated junk before the first update)
display.set_layer(0)
display.set_pen(getPen('bg', BRIGHTNESS))
display.clear()
display.set_pen(getPen('text', BRIGHTNESS))
text = "Initialising!"
textW = display.measure_text(text, 3)
display.text(text, int(240-textW/2), 6, textW, 3)
presto.update()

class UIView(ui.UIBase):
    pass

class UIButton(ui.UIBase):
    def __init__(self, key, x, y, w, h):
        super().__init__(key, x, y)
        self.w, self.h = w, h

    def drawThis(self, display, ctx, x, y):
        display.set_pen(ctx["pen_text"])
        polygon = Polygon()
        polygon.rectangle(x, y, self.w, self.h, (5,5,5,5), 3)
        vector.draw(polygon)

    def isTouched(self, x, y):
        return x>=0 and x<=self.w and y>=0 and y<=self.h

class UIDayToView(ui.UIBase):
    def __init__(self, key, x, y, year, month, day):
        super().__init__(key, x, y)

        monthNames = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        self.monthText = f"{monthNames[VIEW_MONTH-1]} {str(VIEW_YEAR)}"
        self.year, self.month, self.day = year, month, day
            
    def drawThis(self, display, ctx, x, y):
        display.set_pen(ctx["pen_text"])

        text = f"{VIEW_DAY}/{VIEW_MONTH}/{VIEW_YEAR}"
        textW = display.measure_text(text, 3)
        display.text(text, x + 168 - math.floor(textW/2), y, textW, 3)
        if (
            self.year in EVENTS_ON_DAYS
            and self.month in EVENTS_ON_DAYS[self.year]
            and self.day in EVENTS_ON_DAYS[self.year][self.month]
        ):
            i = 0
            for eventID in EVENTS_ON_DAYS[self.year][self.month][self.day]:
                display.text(EVENTS[eventID]["summary"], x + 20, y + 32 + i*20)
                i = i + 1
                    
class UIMonthToView(ui.UIBase):
    def __init__(self, key, x, y, year, month):
        super().__init__(key, x, y)

        monthNames = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        self.monthText = f"{monthNames[VIEW_MONTH-1]} {str(VIEW_YEAR)}"

        iDay=datetime.date(year, month, 1).weekday()
        daysInMonth = getDaysInMonth(year, month)
    
        for i in range(1, daysInMonth + 1):
            xDay = 48*(iDay%7)
            yDay = 66*math.floor(iDay/7) + 56
            self.addChild(UIDayInMonth({"type": "day", "year": year, "month": month, "day": i}, xDay, yDay, i, month, year))
            iDay=iDay+1
            
    def drawThis(self, display, ctx, x, y):
        display.set_pen(ctx["pen_text"])

        textW = display.measure_text(self.monthText, 3)
        display.text(self.monthText, x + 168 - math.floor(textW/2), y, textW, 3)

        dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, dayName in enumerate(dayNames):
            display.text(dayName, x + i*48 + 6, y+32)

class UIDayInMonth(ui.UIBase):
    def __init__(self, key, x, y, dayOfMonth, month, year):
        super().__init__(key, x, y)
        self.dayOfMonth = dayOfMonth
        self.month = month
        self.year = year
        self.text = f"{dayOfMonth:02d}"
        
    def drawThis(self, display, ctx, x, y):
        isToday = (ctx["localtime"][0] == self.year and ctx["localtime"][1] == self.month and ctx["localtime"][2] == self.dayOfMonth)

        pen = ctx["pen_day_bg"]
        if isToday:
            pen = ctx["pen_day_bg_today"]
        display.set_pen(pen)
        display.rectangle(x, y, 44, 60)    

        display.set_pen(ctx["pen_day_text"])
        display.text(self.text, x+4, y+2)

        if (
            self.year in EVENTS_ON_DAYS
            and self.month in EVENTS_ON_DAYS[self.year]
            and self.dayOfMonth in EVENTS_ON_DAYS[self.year][self.month]
        ):
            display.text(f"{len(EVENTS_ON_DAYS[self.year][self.month][self.dayOfMonth])}", x+24, y+34)

    def isTouched(self, x, y):
        return x>=0 and x<=44 and y>=0 and y<=44

# This is a crazy thing to have to do, but *¯\_(ツ)_/¯* Python!
# https://stackoverflow.com/questions/42950/get-the-last-day-of-the-month
def getDaysInMonth(year, month):
    date = datetime.date(year, month, 1)
    # The day 28 exists in every month. 4 days later, it's always next month
    nextMonth = date.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return (nextMonth.replace(day=1) - date).days

if not presto.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
    print("Could not connect")

try:
    ntptime.settime()
    print("NTP Time sync")
except OSError:
    print("Unable to contact NTP server")

today = datetime.date.today()
VIEW_TYPE = "month" # "day" | "month"
VIEW_YEAR, VIEW_MONTH, VIEW_DAY = today.year, today.month, today.day

EVENTS=[]
EVENTS_ON_DAYS={}
def readICS(url):
    res = urequests.get(url)
    # #TODO Check res is ok
    vEventOpen = False
    summary = None
    dtStart = None
    dtEnd = None
    for line in res.text.splitlines():
        if not vEventOpen:
            if line == "BEGIN:VEVENT":
                vEventOpen = True
        else:
            if line == "END:VEVENT":
                vEventOpen = False
                iEvent = len(EVENTS)
                EVENTS.append({"summary": summary, "start": dtStart, "end": dtEnd})
                addEventToLookup(dtStart, dtEnd, iEvent)
                summary = None
                dtStart = None
                dtEnd = None
            elif line.startswith("SUMMARY:"):
                summary = line[8:]
            elif line.startswith("DTSTART"):
                dtStart = line.split(':')[-1]
            elif line.startswith("DTEND"):
                dtEnd = line.split(':')[-1]
    res.close()

    print(f"Found {len(EVENTS)} events")

def addEventToLookup(start, end, iEvent):
    year, month, dayOfMonth = getDateTimeFromString(start)
    if not year in EVENTS_ON_DAYS:
        EVENTS_ON_DAYS[year] = {}
    if not month in EVENTS_ON_DAYS[year]:
        EVENTS_ON_DAYS[year][month] = {}
    if not dayOfMonth in EVENTS_ON_DAYS[year][month]:
        EVENTS_ON_DAYS[year][month][dayOfMonth] = []
    EVENTS_ON_DAYS[year][month][dayOfMonth].append(iEvent)
        
# TODO: Get time when it exists!
def getDateTimeFromString(dtstr):
    return (int)(dtstr[0:4]), (int)(dtstr[4:6]), (int)(dtstr[6:8])

for source in config.ICS_SOURCES:
    readICS(source)

touch = presto.touch
updateScreen = True
DISPLAYED_MINUTE = None
BRIGHT_TIME = time.time()
VIEW = UIView("view", 0, 0)

while True:
    t = time.localtime()
    if DISPLAYED_MINUTE != t[4]:
        updateScreen = True
        
    touch.poll()
    if touch.state:
        BRIGHT_TIME = time.time()
        key = VIEW.getTouch(touch.x, touch.y)
        if key != None:
            if key["type"] == "nav":
                if key["value"] == "settings":
                    pass
                elif key["value"] == "month":
                    VIEW_TYPE = "month"
                elif key["value"] == "month-1":
                    VIEW_MONTH = VIEW_MONTH - 1
                    if VIEW_MONTH < 1:
                        VIEW_MONTH = 12
                        VIEW_YEAR = VIEW_YEAR - 1
                elif key["value"] == "month+1":
                    VIEW_MONTH = VIEW_MONTH + 1
                    if VIEW_MONTH > 12:
                        VIEW_MONTH = 1
                        VIEW_YEAR = VIEW_YEAR + 1
                elif key["value"] == "day-1":
                    VIEW_DAY = VIEW_DAY - 1
                    if VIEW_DAY < 1:
                        VIEW_DAY = 28
                        VIEW_MONTH = VIEW_MONTH - 1
                elif key["value"] == "day+1":
                    VIEW_DAY = VIEW_DAY + 1
                    if VIEW_DAY > 28:
                        VIEW_DAY = 1
                        VIEW_MONTH = VIEW_MONTH + 1
                    
            elif key["type"] == "day":
                VIEW_TYPE, VIEW_YEAR, VIEW_MONTH, VIEW_DAY = "day", key["year"], key["month"], key["day"]
            
        updateScreen = True

    wasBrightness = BRIGHTNESS
    if time.time() - BRIGHT_TIME > DIM_TIME_IN_S:
        BRIGHTNESS = 'dim'
    else:
        BRIGHTNESS = 'regular'
    
    if BRIGHTNESS != wasBrightness:
        updateScreen = True

    if updateScreen:     
        display.set_layer(0)
        display.set_pen(getPen('bg', BRIGHTNESS))
        display.clear()

        if VIEW_TYPE == "month":
            VIEW = UIView("view", 0, 0)
            VIEW.addChild(UIButton({"type": "nav", "value": "settings"}, 420,0, 60,60))
            VIEW.addChild(UIButton({"type": "nav", "value": "month-1"}, 0,66, 60,390))
            VIEW.addChild(UIButton({"type": "nav", "value": "month+1"}, 420,66, 60,390))
            VIEW.addChild(UIMonthToView({"type": "month"}, 72, 10, VIEW_YEAR, VIEW_MONTH))
        
        elif VIEW_TYPE == "day":
            VIEW = UIView("view", 0, 0)
            VIEW.addChild(UIButton({"type": "nav", "value": "month"}, 420,0, 60,60))
            VIEW.addChild(UIButton({"type": "nav", "value": "day-1"}, 0,66, 60,390))
            VIEW.addChild(UIButton({"type": "nav", "value": "day+1"}, 420,66, 60,390))
            VIEW.addChild(UIDayToView({"type": "day-to-view"}, 72, 10, VIEW_YEAR, VIEW_MONTH, VIEW_DAY))

        # Clock
        display.set_pen(getPen('text', BRIGHTNESS))
        text = f"{t[2]:02d}/{t[1]:02d}/{t[0]} {t[3]:02d}:{t[4]:02d}"
        textW = display.measure_text(text)
        display.text(text,480-8-textW,480-20)
        DISPLAYED_MINUTE = t[4]

        VIEW.draw(display, {
                "localtime": time.localtime(),
                "pen_text": getPen('text', BRIGHTNESS),
                "pen_day_bg": getPen('day_bg', BRIGHTNESS),
                "pen_day_bg_today": getPen('day_bg_today', BRIGHTNESS),
                "pen_day_text": getPen('day_text', BRIGHTNESS),
            }, 0,0
        )

        presto.update()
        updateScreen = False
    
    time.sleep(1/15)
