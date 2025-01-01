# Calendar

A basic calendar view for [Pimoroni Presto](https://shop.pimoroni.com/products/presto?variant=54894104019323)

## Guarantees and Warranty

None! :)

## Running

### Config

Copy `_config.py` to `config.py` and set your Wifi SSID and Password.

You can also set URLs in the ICS_SOURCES list. These will be loaded on startup.

For Google Calendar, follow [the instructions: Sync or view your calendar -> Get your calendar (view only)](https://support.google.com/calendar/answer/37648?hl=en#zippy=%2Cget-your-calendar-view-only)

### Upload

Upload `main.py` and `config.py` to the Presto if you'd like it to be the default booting program.

The program should connect to Wifi, sync NTP time, and display a calendar view, highlighting the current day.

Touch the button on the left side of the screen to go back a month and the right side to advance.

There's a settings button in the top right corner. Press this to choose a skin (currently light or dark).

If the calendar is left for 30 seconds, it dims. Press the centre of the screen to wake it.

## Issues

- Events with timezones timestamps are ignored
- Events that run over multiple days should do so
- Should have a 'return to today'
- In month view, at 00:00, the day should update
- Should have a button / auto-refresh calendar
- Interruptable web request for calendar sync?
- Occasionally, NTP Time sync will fail.
- Maybe VIEW_YEAR, VIEW_MONTH, VIEW_DAY should be collapsed into a Date object