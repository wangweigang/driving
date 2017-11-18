""" car.py
    car kenetics
    modified based on https://cs.iupui.edu/~aharris/pygame/ch09/carVec.py
    and http://engineeringdotnet.blogspot.de/2010/04/simple-2d-car-physics-in-games.html
"""
import pygame
import numpy as np
import random
import os, sys, time
import re
#import watchLog as wf
import win32file
import win32con

#from numba import vectorize, cuda
if np.size(sys.argv) > 1:
    controlParGlbl = np.int32(sys.argv[1])
else:
    controlParGlbl = np.int32(0)
    
pygame.init()

# deal with log reading
if controlParGlbl==1:
    path2WatchGlbl = r"H:\Projects\bomb\Me\canoe\Test" # look at the current directory
    file2WatchGlbl = "secondaryLocation.asc" # look for changes to a file called test.txt
       
#   Open the file we're interested in
    hOfFileGlbl = open(os.path.join(path2WatchGlbl, file2WatchGlbl), "rb")

#   Throw away any exising log data
    hOfFileGlbl.read()

    # Set up the bits we'll need for output
    ACTIONS = {
          1 : "Created",
          2 : "Deleted",
          3 : "Updated",
          4 : "Renamed from something",
          5 : "Renamed to something"
    }

    FILE_LIST_DIRECTORY = 0x0001

    hDirGlbl = win32file.CreateFile (
          path2WatchGlbl,
          FILE_LIST_DIRECTORY,
          win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
          None,
          win32con.OPEN_EXISTING,
          win32con.FILE_FLAG_BACKUP_SEMANTICS,
          None
    )
 
def waitAkey(): event = pygame.event.wait()
    
def getKinetics():
    kineticsOfCar = []
#   Wait for a change to occur
    results = win32file.ReadDirectoryChangesW (
              hDirGlbl,
              1024,
              False,
              win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
              None,
              None
    )

#   For each change, check to see if it's updating the file we're interested in
    for action, file in results:
#       full_filename = os.path.join (path2WatchGlbl, file)
        print (file, ACTIONS.get (action, "Unknown"))
        if file == file2WatchGlbl:
            first = hOfFileGlbl.readline()        # Read the first line.
            hOfFileGlbl.seek(-2, os.SEEK_END)     # Jump to the second last byte.
            while hOfFileGlbl.read(1) != b"\n":   # Until EOL is found...
                hOfFileGlbl.seek(-2, os.SEEK_CUR) # ...jump back the read byte plus one more.
            lineLast      = hOfFileGlbl.readline().decode()         # Read last line.
#            print("1: ", first)
            #print("2: ", lineLast)
            kineticsOfCar = processData(lineLast)
#            lineNew = hOfFileGlbl.read()
#            if lineNew != "":
#                kineticsOfCar = processData(lineNew)
#                break

    return kineticsOfCar

# define the calss for car properties and operation
class Car:
    def __init__(self, screen):
        self.screen      = screen
        self.imageMaster = pygame.image.load("cayenne05.png")
        self.image       = self.imageMaster
        # Image parameters
        #
        # self.imageMaster = self.imageMaster.convert()
        # self.imageMaster = pygame.transform.scale(self.imageMaster, (226/2, 487/2))
        # self.imageMaster = pygame.transform.scale(self.imageMaster, (111,55))
        self.rect        = self.imageMaster.get_rect()
        self.height      = self.imageMaster.get_width()
        self.width       = self.imageMaster.get_height()
        
        # screen parameters
        self.widthScreen  = self.screen.get_width()
        self.heightScreen = self.screen.get_height()
        
        # car paremeters
        self.offsetSec  = -86.8  # offset of secondary coil
        self.base       = 284 # / (487/55)
        self.dt         = 0.01
        self.carHeading = -np.pi/2   # initial orientation
        self.direction  = 0
        self.turnRate   = 3
        self.accel      = 1
        self.initX      = random.randrange(-22,22) + int(0.5*self.widthScreen-0.5*self.width)
        self.initY      = (self.heightScreen-0.4*self.height) # 300.0
        self.position   = np.array([self.initX,self.initY])
        self.rect.center= tuple(self.position)
        self.speed      = 0
        
        # steering decay
        self.steeringDecayMax = 30   # number of dt 
        self.steeringCounter  = 0
        self.returnRate       = 2
        self.keyLeft          = False
        self.keyRight         = False
           
        # control parameters
        self.drivenBy = controlParGlbl  # 0: keyborard; 1: log file
        
        # parameters of second coil: the initial position of the car is facing east
        # W:1.95m L:4.87m  W:206px L:486px  px/m = 100 
        positionX     = 78                      # pixel   
        positionY     = 0.5*self.height         # pixel
        widthOfSec    = 35                      # pixel
        heightOfSec   = 25                      # pixel
        
    def update(self): # for every frame
        self.checkControlKeys()
        if self.drivenBy == 1: # driven by log file change
            # self.direction self.carHeading, self.speed, self.position
            kineticsOfCar = getKinetics()
            if len(kineticsOfCar)>0:
                self.speed      = kineticsOfCar[1]
                self.accel      = kineticsOfCar[2]
                self.carHeading = kineticsOfCar[3]
                self.direction  = kineticsOfCar[4]
                print("                              carKineC:", self.speed, self.accel, self.carHeading, self.direction)
        else:
            self.checkMoveKeys()
            #print("                              carKineK:", self.speed, self.accel, self.carHeading, self.direction)

        self.positionNew()
        self.checkBounds()
        self.rect.center = tuple(self.position)
        
    def checkMoveKeys(self):
        keys = pygame.key.get_pressed()
        # steering
        if keys[pygame.K_RIGHT]:
            self.keyRight = True
            self.steeringCounter  = 0
            self.direction += self.turnRate
            self.direction  = np.max([self.direction, -90])
            
        if keys[pygame.K_LEFT]:
            self.keyLeft = True
            self.steeringCounter  = 0
            self.direction -= self.turnRate
            self.direction  = np.min([self.direction, 90])
            

            # accelerating/deaccelerating        
        if keys[pygame.K_UP]:
            self.speed += self.accel
        if keys[pygame.K_DOWN]:
            self.speed -= self.accel
        if abs(self.speed)<self.accel:
            self.speed  = 0
            
        self.speed = np.sign(self.speed)*np.min([80, np.abs(self.speed)])
        
        #print("speed:", self.speed, self.accel)

    def checkControlKeys(self):
        
        keys = pygame.key.get_pressed()        
        # resetBackground and pause
        if keys[pygame.K_r]:
            self.speed = 0
            self.direction   = 0
            self.initX = random.randrange(-22,22) + int(0.5*self.widthScreen-0.5*self.width)
            self.position   = (self.initX,self.initY)
            self.carHeading = -np.pi/2
            time.sleep(0.2)

        if keys[pygame.K_b]:
            self.speed = 0

        if keys[pygame.K_q]:
            print("\nExit from AlignMe,")
            sys.exit()
            
            
    def positionNew(self):

        radians1        = self.carHeading
        # if radians1<-np.pi: 
            # radians1 = radians1
        frontWheel      = self.position + 0.5*self.base*np.array([np.cos(radians1), np.sin(radians1)])

        backWheel       = self.position - 0.5*self.base*np.array([np.cos(radians1), np.sin(radians1)])
        backWheel      += self.speed * self.dt * np.array([np.cos(radians1), np.sin(radians1)])

        radians         = (self.carHeading + self.direction*np.pi/180)
        frontWheel     += self.speed * self.dt * np.array([np.cos(radians), np.sin(radians)])
        self.position   = 0.5 * (frontWheel + backWheel) 
        # 
        self.carHeading = np.arctan2((frontWheel[1]-backWheel[1]), frontWheel[0]-backWheel[0])
        carHeadingDeg   = -np.rad2deg(self.carHeading)  # 

        self.image      = pygame.transform.rotate(self.imageMaster, carHeadingDeg)  # carHeadingDeg>0 --> counterclockwise
#        print("sads: {:5.1f} {:5.1f} {:5.1f} {:5.1f} {:5.1f} {:5.1f} ".format(self.speed, self.accel,
#               np.rad2deg(radians1), np.rad2deg(radians), np.rad2deg(self.carHeading), self.direction), self.position)
        
        # if np.abs(radians1-radians)>1.57: waitAkey()
        
        if (self.keyRight or self.keyLeft) and (self.steeringCounter<self.steeringDecayMax):
            self.steeringCounter += 1
            dirTemp               = self.direction
#            self.direction             *= 0.85
            self.direction        = self.direction - np.sign(self.direction)*self.returnRate
            if dirTemp*self.direction<0: self.direction = 0
        else:
            self.keyLeft          = False
            self.keyRight         = False
            self.steeringCounter  = 0
            self.direction        = 0
      
    def checkBounds(self):
        rectIma = self.image.get_rect()
        if self.position[0]+0.7*rectIma.width > self.screen.get_width():
            self.position[0] = self.screen.get_width() - 0.7*rectIma.width
        if self.position[0]+0.5*rectIma.width < 0:
            self.position[0] = -0.5*rectIma.width
        if self.position[1]+0.8*rectIma.centery>self.screen.get_height():
            self.position[1] = self.screen.get_height() - 0.8*rectIma.centery
        if self.position[1]<0:
            self.position[1] = 0


    def resetBackground(self, screen):
        screen.fill((244, 244, 244))
        # put primary there
        self.placePrimary(screen)
        #self.drawRay(screen, self.image)
        
    def placePrimary(self,screen):
        x = 153
        y = 201-44
        w = 44+8
        h = 55+8
        color = (222,222,222)
        pygame.draw.rect(screen, color, [x, y, w, h])

        x = 157
        y = 205-44
        w = 44
        h = 55
        color = (99,99,99)
        pygame.draw.rect(screen, color, [x, y, w, h])
    
    def drawCar(self, screen):
        #print("xya:{:5.1f} {:5.1f} {:5.1f}".format(self.x, self.y, self.direction))
        screen.blit(self.image, tuple(self.position))
    
    def drawRay(self, screen):
        xSensor = int(self.widthScreen/2+3)
        ySensor = int(self.heightScreen/2-33)
        color   = (255,200,0)
        rectIma = self.image.get_rect()
        # center of secondary coil
        x0      = self.position[0]+rectIma.centerx
        y0      = self.position[1]+rectIma.centery
        xc      = x0 - self.offsetSec * np.cos(self.carHeading)
        yc      = y0 - self.offsetSec * np.sin(self.carHeading)
        l       = np.sqrt(16.5*16.5 + 10.5*10.5)
        alpha   = np.arctan2(10.5, 16.5)
        #pygame.draw.line(screen, color,(xSensor,ySensor), (xc, yc), 1)
        distance = []
        
        pygame.draw.line(screen, color,(xSensor,ySensor), (xc,yc), 1)
        #  0----1
        #  |    |
        #  3----2
        xy = (xc+l*np.sin(alpha+self.carHeading), yc-l*np.cos(alpha+self.carHeading))    # 0
        pygame.draw.line(screen, color,(xSensor,ySensor), xy, 1)
        distance.append(np.sqrt((xy[0]-xSensor)**2 + (xy[1]-ySensor)**2 ))
        xy = (xc+l*np.sin(alpha-self.carHeading), yc+l*np.cos(alpha-self.carHeading))    # 1
        pygame.draw.line(screen, color,(xSensor,ySensor), xy, 1)
        distance.append(np.sqrt((xy[0]-xSensor)**2 + (xy[1]-ySensor)**2 ))
        xy = (xc-l*np.sin(alpha+self.carHeading), yc+l*np.cos(alpha+self.carHeading))    # 2
        pygame.draw.line(screen, color,(xSensor,ySensor), xy, 1)
        distance.append(np.sqrt((xy[0]-xSensor)**2 + (xy[1]-ySensor)**2 ))
        xy = (xc-l*np.sin(alpha-self.carHeading), yc-l*np.cos(alpha-self.carHeading))    # 3
        pygame.draw.line(screen, color,(xSensor,ySensor), xy, 1)
        distance.append(np.sqrt((xy[0]-xSensor)**2 + (xy[1]-ySensor)**2 ))
        textTemp = int(sum(distance)/float(len(distance)))   # faster then np.mean
        placeText(textTemp, (230, 8), screen)
                
        # pygame.draw.line(screen, color,(xSensor,ySensor), (x0, y0), 1)
        # pygame.draw.line(screen, color,(xSensor,ySensor), (x0, y[0]), 1)
        # pygame.draw.line(screen, color,(xSensor,ySensor), (xc, yc), 1)
        # pygame.draw.line(screen, color,(xSensor,ySensor), (x[2], y[2]), 1)
        # pygame.draw.line(screen, color,(xSensor,ySensor), (x0, y[3]), 1)
        # print("xy", centerX,centerY, np.rad2deg(self.carHeading), np.cos(self.carHeading))
         
def processData(lineNew):
# parse the string to float
    # stringSplit = re.sub("[^0-9^.^\s]", "", lineNew)
    stringSplit = ' '.join(lineNew.split())
    stringSplit = stringSplit.split(" ")
    stringSplit = np.array(stringSplit)
    valSplit    = stringSplit.astype(np.float)
    if len(valSplit) == 5:
        # print("read:   ", valSplit, len(valSplit))
    # scale the physical data to screen unit
    # Time Speed[kmh] Acceleration[m/s/s] Direction[deg] Steering_Angle[deg] 
    # scale  20:0,2          0.1:1                1:1             1:1 
        scale       = np.array([0, 20/0.2, 0.1/1, 1/1, 1/1])
        valSplit    = scale*valSplit
        # print("scaled: ", valSplit)
    else:
        print("read but number not match: ", valSplit)
    return valSplit

    
    
def placeText(text, xy, screen):
    font      = pygame.font.Font(None,24)
    textWhole = font.render("eDistance:"+str(text), 1, (11,11,11))
    screen.blit(textWhole, xy)

       
def main():
    print("\nStaring AlignMe ... ...")
    
    screen = pygame.display.set_mode((350, 500))
    pygame.display.set_caption("AlignMe")
    
    background = pygame.Surface(screen.get_size())
    background.fill((244, 244, 244))
    
    screen.blit(background, (0, 0))
    
    car = Car(screen)
    #car = pygame.sprite.Group(car)
    
    keepGoing = True
    clock     = pygame.time.Clock()
    
    while keepGoing:
        clock.tick(1/car.dt)
        
        # way to get out
        for event in pygame.event.get():
            if event.type == pygame.QUIT:   # the small "x" on the window upper-right corner
                keepGoing = False

        car.resetBackground(screen)
        
        car.update()
# plot sensor rays
        car.drawRay(screen)
        
        car.drawCar(screen)

        pygame.display.update()
        # waitAkey()
        
        
if __name__ == "__main__":
    main()
    