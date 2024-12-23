# https://github.com/creativenucleus/rpi-public

import datetime
import math
import time
import config
import network
import ntptime
import sys

from presto import Presto

presto = Presto(True)
display = presto.display

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

class Day:
    def __init__(self, x, y, w, h, dayOfMonth):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.dayOfMonth = dayOfMonth

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
        days.append(Day(int(x),int(y),int(w),int(h),i+1))
        iDay=iDay+1

if not presto.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
    print("Could not connect")
try:
    ntptime.settime()
    print("NTP Time sync")
except OSError:
    print("Unable to contact NTP server")

today = datetime.date.today()
VIEW_YEAR, VIEW_MONTH = today.year, today.month

initDays(VIEW_YEAR, VIEW_MONTH)

touch = presto.touch
updateScreen = True
DISPLAYED_MINUTE = None
BRIGHT_TIME = time.time()

while True:
    t = time.localtime()
    if DISPLAYED_MINUTE != t[4]:
        updateScreen = True
        
    touch.poll()
    if touch.state:
        BRIGHT_TIME = time.time()
        if touch.x < 100:
            VIEW_MONTH = VIEW_MONTH - 1
            if VIEW_MONTH < 1:
                VIEW_MONTH = 12
                VIEW_YEAR = VIEW_YEAR - 1
        elif touch.x > 380:
            VIEW_MONTH = VIEW_MONTH + 1
            if VIEW_MONTH > 12:
                VIEW_MONTH = 1
                VIEW_YEAR = VIEW_YEAR + 1
        initDays(VIEW_YEAR, VIEW_MONTH)
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

        display.set_pen(getPen('text', BRIGHTNESS))
        monthNames = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        text = f"{monthNames[VIEW_MONTH-1]} {str(VIEW_YEAR)}"
        textW = display.measure_text(text, 3)
        display.text(text, int(240-textW/2), 6, textW, 3)

        dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, dayName in enumerate(dayNames):
            display.text(dayName, 16 + i*68, 38)
            
        for day in days:
            if t[0] == VIEW_YEAR and t[1] == VIEW_MONTH and t[2] == day.dayOfMonth:
                display.set_pen(getPen('day_bg_today', BRIGHTNESS))
            else:
                display.set_pen(getPen('day_bg', BRIGHTNESS))
            display.rectangle(day.x, day.y, day.w, day.h)
            
            display.set_pen(getPen('day_text', BRIGHTNESS))
            display.text(f"{day.dayOfMonth:02d}", day.x+4, day.y+4)

        display.set_pen(getPen('text', BRIGHTNESS))
        text = f"{t[2]:02d}/{t[1]:02d}/{t[0]} {t[3]:02d}:{t[4]:02d}"
        textW = display.measure_text(text)
        display.text(text,480-8-textW,480-20)
        DISPLAYED_MINUTE = t[4]

        presto.update()
        updateScreen = False
    
    time.sleep(1/15)
