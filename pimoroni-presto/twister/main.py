from presto import Presto
from math import sin, pi
import time

presto = Presto(ambient_light=True)
display = presto.display
display.set_backlight(.001)

PENBG = display.create_pen(0, 0, 0)

while True:
    display.set_layer(0)
    display.set_pen(PENBG)
    display.clear()
    
    t = time.ticks_us()*0.000001
    d1, d2, d3 = pi*.5, pi, pi*1.5
    for y in range(0,239, 3):
        ysh = y*sin(t*.3)*0.03+sin(t*.4)*5
        x0 = 120+sin(ysh + t*.1)*50+sin(ysh + t*.33)*30
        x1 = int(x0 + sin(ysh)*30)
        x2 = int(x0 + sin(ysh + d1)*30)
        x3 = int(x0 + sin(ysh + d2)*30)
        x4 = int(x0 + sin(ysh + d3)*30)

        if x1 > x2:
            display.set_pen(display.create_pen(int(127+sin(y*.02 - t*1.1)*127), 0, 128))
            display.line(x1,y,x2,y)
        if x2 > x3:
            display.set_pen(display.create_pen(128, 0, int(127-sin(y*.02 - t*1.6)*127)))
            display.line(x2,y,x3,y)
        if x3 > x4:
            display.set_pen(display.create_pen(int(127-sin(y*.02 + t*1.9)*127), 0, 128))
            display.line(x3,y,x4,y)
        if x4 > x1:
            display.set_pen(display.create_pen(128, 0, int(127+sin(y*.02 + t*1.4)*127)))
            display.line(x4,y,x1,y)
    
    presto.update()
    