# https://github.com/creativenucleus/rpi-public

import datetime
import math
import time
import config
import ntptime
import sys
import re
import urequests
import ui

from presto import Presto
from picovector import PicoVector, Polygon

presto = Presto(full_res=True)
display = presto.display
vector = PicoVector(display)

LOG = []
DIM_TIME_IN_S = 30

SKIN = 'light'
SKINS={
    'dark': {
        'name': "Dark",
        'bg': (20, 0, 60),
        'text': (255, 255, 255),
        'day_bg': (200, 200, 200),
        'day_bg_today': (255, 255, 128),
        'day_text': (0, 0, 60),
    },
    'light': {
        'name': "Light",
        'bg': (200, 200, 200),
        'text': (0, 0, 30),
        'day_bg': (255, 255, 255),
        'day_bg_today': (255, 255, 128),
        'day_text': (0, 0, 60),
    },
}

def getPen(use):
    rgb = SKINS[SKIN][use]
    return display.create_pen(rgb[0], rgb[1], rgb[2])

def showLog(text, abort=False):
    global LOG
    LOG.append(text)

    display.set_layer(0)
    if abort:
        display.set_pen(display.create_pen(120, 0, 0))
    else:
        display.set_pen(getPen('bg'))
    display.clear()
    display.set_pen(getPen('text'))

    y = 20
    for logItem in LOG:
        print(logItem)
        display.text(logItem, 20, y, 440, 3)
        y = y + 20
    presto.update()
    if abort:
        time.sleep(10)
        sys.exit()

    
showLog("[Initialising]")


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

class UIIconButton(UIButton):
    def __init__(self, key, x, y, w, h, type):
        super().__init__(key, x, y, w, h)
        self.type = type

    def drawThis(self, display, ctx, x, y):
        super().drawThis(display, ctx, x, y)
        if self.type == "left":
            display.set_pen(ctx["pen_text"])
            polygon = Polygon()
            mx, my = x+self.w/2, y+self.h/2
            polygon.path((mx+20, my-20), (mx-20, my), (mx+20, my+20))
            vector.draw(polygon)
        elif self.type == "right":
            display.set_pen(ctx["pen_text"])
            polygon = Polygon()
            mx, my = x+self.w/2, y+self.h/2
            polygon.path((mx-20, my-20), (mx+20, my), (mx-20, my+20))
            vector.draw(polygon)
        elif self.type == "settings":
            display.set_pen(ctx["pen_text"])
            polygon = Polygon()
            mx, my = x+self.w/2, y+self.h/2
            polygon.star(mx, my, 4, 10, 25)
            vector.draw(polygon)
        elif self.type == "month":
            display.set_pen(ctx["pen_text"])
            polygon = Polygon()
            mx, my = x+self.w*.5, y+self.h*.5
            mw, mh = self.w*.7, self.h*.5
            polygon.rectangle(mx-mw/2, my-mh/2, mw, mh, corners=(4, 4, 4, 4), stroke=3)
            vector.draw(polygon)

class UISkinButton(UIButton):
    def __init__(self, key, x, y, w, h, name):
        super().__init__(key, x, y, w, h)
        self.name = name

    def drawThis(self, display, ctx, x, y):
        super().drawThis(display, ctx, x, y)
        display.set_pen(ctx["pen_text"])
        display.text(self.name, x + 8, y + 4)
        skinID = self.key["skin"]
        for i, penID in enumerate(["bg", "text", "day_bg", "day_bg_today", "day_text"]):
            rgb = SKINS[skinID][penID]
            display.set_pen(display.create_pen(rgb[0], rgb[1], rgb[2]))
            display.rectangle(8 + x + i * 24, 24 + y, 20, 20)

# Month input is 1-12
def getMonthName(iMonth):
    monthNames = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
    return monthNames[iMonth - 1]

def eventsComparator(e):
    print(e)
    if e["start"]["time"] == None:
        return -1	# Put these first
    t = e["start"]["time"]
    return t["h"] * 3600 + t["m"] * 60 + t["s"]

class UIDayToView(ui.UIBase):
    def __init__(self, key, x, y, year, month, day):
        super().__init__(key, x, y)
        self.year, self.month, self.day = year, month, day
            
    def drawThis(self, display, ctx, x, y):
        display.set_pen(ctx["pen_text"])

        text = f"{VIEW_DAY} {getMonthName(VIEW_MONTH)} {VIEW_YEAR}"
        textW = display.measure_text(text, 3)
        display.text(text, x + 168 - math.floor(textW/2), y, textW, 3)
        if (
            self.year in EVENTS_ON_DAYS
            and self.month in EVENTS_ON_DAYS[self.year]
            and self.day in EVENTS_ON_DAYS[self.year][self.month]
        ):
            # Get the events from our IDs and sort them by time...
            events = []
            for eventID in EVENTS_ON_DAYS[self.year][self.month][self.day]:
                events.append(EVENTS[eventID])
            
            events.sort(key=lambda x: eventsComparator(x))

            i = 0
            for event in events:
                lineY = y + 32 + i*20
                if event["start"]["time"] != None:
                    time = event["start"]["time"]
                    text = f"{time['h']:02d}:{time['m']:02d}"
                    display.text(text, x + 20, lineY)
                # TODO: clip and/or multiline
                display.text(event["summary"], x + 80, lineY, 260)
                i = i + 1

class UIMonthToView(ui.UIBase):
    def __init__(self, key, x, y, year, month):
        super().__init__(key, x, y)

        self.monthText = f"{getMonthName(VIEW_MONTH)} {str(VIEW_YEAR)}"

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
        display.text(self.text, x+4, y+2, 0, 3)

        if (
            self.year in EVENTS_ON_DAYS
            and self.month in EVENTS_ON_DAYS[self.year]
            and self.dayOfMonth in EVENTS_ON_DAYS[self.year][self.month]
        ):
            display.text(f"{len(EVENTS_ON_DAYS[self.year][self.month][self.dayOfMonth])}", x+34, y+40)

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

showLog("Connecting to WiFi...")
if not presto.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
    showLog("Could not connect", True)	#NB I don't think this will trigger - connect (at the moment) is a loop
showLog("Connected")

showLog("NTP Time Sync...")
try:
    ntptime.settime()
    showLog("NTP Time Sync: Done")
except OSError:
    showLog("NTP Time Sync: Unable to contact server", True)

today = datetime.date.today()
VIEW_TYPE = "month" # "day" | "month"
VIEW_YEAR, VIEW_MONTH, VIEW_DAY = today.year, today.month, today.day

EVENTS=[]
EVENTS_ON_DAYS={}
def readICS(url):
    res = urequests.get(url)
    # #TODO Check result is ok

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
                if dtStart != None and dtEnd != None:
                    iEvent = len(EVENTS)
                    EVENTS.append({"summary": summary, "start": dtStart, "end": dtEnd})
                summary = None
                dtStart = None
                dtEnd = None
            elif line.startswith("SUMMARY:"):
                summary = line[8:]
            elif line.startswith("DTSTART"):
                dtStart = decodeDTFromICS(line.split(':')[-1])
                if dtStart == None:
                    print(f"Could not read datetime: {line}")
            elif line.startswith("DTEND"):
                dtEnd = decodeDTFromICS(line.split(':')[-1])
                if dtEnd == None:
                    print(f"Could not read datetime: {line}")
    res.close()

    print(f"Found {len(EVENTS)} events")

def indexEventsByDate():
    for iEvent, event in enumerate(EVENTS):
        addEventToLookup(event["start"], event["end"], iEvent)

# handles 20241227 or 20241227T123456Z
# TODO: DTSTART;TZID=Europe/London:20241126T100000
RE_DT = re.compile(r"^(\d\d\d\d)(\d\d)(\d\d)(T(\d\d)(\d\d)(\d\d)Z)?$")
def decodeDTFromICS(raw):
    match = RE_DT.match(raw)
    if match == None:
        return None   
    groups = match.groups()
    out = {"date":{"y": int(groups[0]), "m": int(groups[1]), "d": int(groups[2])}, "time": None}
    if groups[3] != None:
        out["time"] = {"h": int(groups[4]), "m": int(groups[5]), "s": int(groups[6])}
    return out

def addEventToLookup(start, end, iEvent):
    dateStart = start["date"]
    year, month, dayOfMonth = dateStart["y"], dateStart["m"], dateStart["d"]
    # TODO: Iterate between two dates
    if not year in EVENTS_ON_DAYS:
        EVENTS_ON_DAYS[year] = {}
    if not month in EVENTS_ON_DAYS[year]:
        EVENTS_ON_DAYS[year][month] = {}
    if not dayOfMonth in EVENTS_ON_DAYS[year][month]:
        EVENTS_ON_DAYS[year][month][dayOfMonth] = []
    EVENTS_ON_DAYS[year][month][dayOfMonth].append(iEvent)
    
for source in config.ICS_SOURCES:
    showLog("Reading Calendar...")
    readICS(source)
    showLog("Reading Calendar: Done")

showLog("Indexing Events...")
indexEventsByDate()
showLog("Indexing Events: Done")

touch = presto.touch
updateDisplay = True
IS_DIMMED = False
DISPLAYED_MINUTE = None
BRIGHT_TIME = time.time()
VIEW = UIView("view", 0, 0)

# This function is a bit jank
# NB monthAdd should be -1,0,1
# NB dayAdd should be -1,0,1
def changeDate(monthAdd, dayAdd):
    global VIEW_YEAR, VIEW_MONTH, VIEW_DAY
    # get a day in the middle of this month and shift it by 20 days either way if needed, then set the day
    date = datetime.date(VIEW_YEAR, VIEW_MONTH, 15) + datetime.timedelta(days=monthAdd*20)
    date = date.replace(day=VIEW_DAY)
    date = date + datetime.timedelta(days=dayAdd)
    VIEW_YEAR, VIEW_MONTH, VIEW_DAY = date.year, date.month, date.day

while True:
    t = time.localtime()
    if DISPLAYED_MINUTE != t[4]:
        updateDisplay = True
        
    touch.poll()
    if touch.state:
        BRIGHT_TIME = time.time()
        key = VIEW.getTouch(touch.x, touch.y)
        if key != None:
            if key["type"] == "skin":
                SKIN = key["skin"]
            if key["type"] == "nav":
                if key["value"] == "settings":
                    VIEW_TYPE = "settings"
                elif key["value"] == "month":
                    VIEW_TYPE = "month"
                elif key["value"] == "month-1":
                    changeDate(-1, 0)
                elif key["value"] == "month+1":
                    changeDate(1, 0)
                elif key["value"] == "day-1":
                    changeDate(0, -1)
                elif key["value"] == "day+1":
                    changeDate(0, 1)
 
            elif key["type"] == "day":
                VIEW_TYPE, VIEW_YEAR, VIEW_MONTH, VIEW_DAY = "day", key["year"], key["month"], key["day"]
                        
        updateDisplay = True

    wasDimmed = IS_DIMMED
    if time.time() - BRIGHT_TIME > DIM_TIME_IN_S:
        IS_DIMMED = True
    else:
        IS_DIMMED = False
    
    if IS_DIMMED != wasDimmed:
        brightness = 1
        if IS_DIMMED:
            brightness = 0.02
        presto.set_backlight(brightness)
        updateDisplay = True

    if updateDisplay:     
        display.set_layer(0)
        display.set_pen(getPen('bg'))
        display.clear()

        if VIEW_TYPE == "settings":
            VIEW = UIView("view", 0, 0)
            VIEW.addChild(UIIconButton({"type": "nav", "value": "month"}, 414,4, 60,60, "month"))
            i = 0
            for skinID, skin in SKINS.items():
                VIEW.addChild(UISkinButton({"type": "skin", "skin": skinID}, 20,66 + i*70, 390, 60, skin["name"]))
                i = i + 1
        elif VIEW_TYPE == "month":
            VIEW = UIView("view", 0, 0)
            VIEW.addChild(UIIconButton({"type": "nav", "value": "settings"}, 414,4, 60,60, "settings"))
            VIEW.addChild(UIIconButton({"type": "nav", "value": "month-1"}, 6,194, 60,132, "left"))
            VIEW.addChild(UIIconButton({"type": "nav", "value": "month+1"}, 414,194, 60,132, "right"))
            VIEW.addChild(UIMonthToView({"type": "month"}, 72, 10, VIEW_YEAR, VIEW_MONTH))
        elif VIEW_TYPE == "day":
            VIEW = UIView("view", 0, 0)
            VIEW.addChild(UIIconButton({"type": "nav", "value": "month"}, 414,4, 60,60, "month"))
            VIEW.addChild(UIIconButton({"type": "nav", "value": "day-1"}, 6,194, 60,132, "left"))
            VIEW.addChild(UIIconButton({"type": "nav", "value": "day+1"}, 414,194, 60,132, "right"))
            VIEW.addChild(UIDayToView({"type": "day-to-view"}, 72, 10, VIEW_YEAR, VIEW_MONTH, VIEW_DAY))

        # Clock
        display.set_pen(getPen('text'))
        text = f"{t[2]:02d}/{t[1]:02d}/{t[0]} {t[3]:02d}:{t[4]:02d}"
        textW = display.measure_text(text)
        display.text(text,480-8-textW,480-20)
        DISPLAYED_MINUTE = t[4]

        VIEW.draw(display, {
                "localtime": time.localtime(),
                "pen_bg": getPen('bg'),
                "pen_text": getPen('text'),
                "pen_day_bg": getPen('day_bg'),
                "pen_day_bg_today": getPen('day_bg_today'),
                "pen_day_text": getPen('day_text'),
            }, 0,0
        )

        if updateDisplay:
            presto.update()
            updateDisplay = False
    
    time.sleep(1/15)                                                                                                 
