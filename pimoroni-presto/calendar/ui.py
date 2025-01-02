# A UI framework

class UIBase:
    def __init__(self, key, x, y):
        self.isHidden = False
        self.key = key
        self.x, self.y = x, y
        self.children = []
    
    def addChild(self, child):
        self.children.append(child)
    
    def draw(self, display, ctx, parentX,  parentY):
        if self.isHidden:
            return
        
        x = parentX + self.x
        y = parentY + self.y
        self.drawThis(display, ctx, x, y)
        for child in self.children:
            child.draw(display, ctx, x, y)
    
    # implement this in your derived class
    def drawThis(self, display, ctx, x, y):
        pass
    
    def getTouch(self, touchX, touchY):
        x = touchX - self.x
        y = touchY - self.y
        if self.isTouched(x, y):
            return self.key
                
        for child in self.children:
            key = child.getTouch(x, y)
            if key != None:
                return key
        
        return None
    
    def isTouched(self, x, y):
        return False
    
class UIText(UIBase):
    def __init__(self, key, x, y, text):
        super().__init__(key, x, y)
        self.text = text
        
    def drawThis(self, display, ctx, x, y):
        pen = display.create_pen(255, 255, 0)
        display.set_pen(pen)
        display.text(self.text, x, y)
            

class UITheme:
    def __init__(self, name):
        self.name = name
        
    def drawBG(self, display, skin):
        pass

class UISkin:
    def __init__(self, name, rgbs):
        self.name = name
        self.rgbs = rgbs

    def getPen(self, display, pen):
        rgb = self.rgbs[pen]
        return display.create_pen(rgb[0], rgb[1], rgb[2])
    