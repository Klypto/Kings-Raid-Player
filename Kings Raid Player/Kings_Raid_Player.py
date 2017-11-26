#!  python3
"""Kings Raid Bot
Kings Raid

A bot program to automatically play the Kings Raid game

This code is awful since this is the first time I've worked with python
"""



#logging.disable(logging.DEBUG) # uncomment to block debug log messages

def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import pip
        try:
            pip.main(['install', package])
        except WindowsError:
            logging.debug('Could not install module:  %s' % (package,))
            logging.debug( 'Please ensure you run as administrator to install dependencies' )
            os.system('pause')
    finally:
        globals()[package] = importlib.import_module(package)

if __name__ == '__main__':
    install_and_import('pywinauto')

import os
import sys
import time
import logging
import random
import copy
import cv2
import win32gui
import win32ui
import matplotlib
import pyautogui
import win32con
import win32api
import subprocess
import tkinter
import pywintypes


from ctypes import windll
from enum import Enum     # for enum34, or the stdlib version
import numpy as np
from matplotlib import pyplot as plt

from pywinauto import application 


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d: %(message)s', datefmt='%H:%M:%S')



Screens = Enum('Screens', 'NONE UNKNOWN BATTLE WORLD RESULTS RAIDLOBBY LOOT RAIDLIST')
Modes = Enum('modes', 'DRAGON IDLE ADVANCE')

# Global variables
GAME_REGION = () # (left, top, width, height) values coordinates of the game window
SCREEN = Screens.NONE # Active Screen
LASTKNOWNSCREEN = Screens.NONE # Active Screen
IMAGES = {} 
IMAGES_SCALED = {}
DEBUG_IMAGE = ()
FONT = cv2.FONT_HERSHEY_SIMPLEX
MODE = Modes.IDLE
BUTTONS = {}
HWND = win32gui.FindWindow(None, "Bluestacks")
LAST_CLICK = time.time()
RAID_OPEN_SLOTS = False
PLAYER_HEALTHBARS = []
LAST_SCREEN_TIME = time.time()
LAST_SCREEN_TRANSITION_TIME = time.time()
hWindow = ()
hdc = ()
STORED_TEXT = []

class Hero:
    def __init__(self, name, facemark, skills):
        self.name = name
        self.facemark = facemark
        self.skills = skills



def main():
    global DEBUG_IMAGE
    global hWindow
    """Runs the entire program. The Kings Raid Program must be on the desktop (not minimized) but can run in the background while you do other things"""
    logging.debug('Program Started. Press F12 to abort at any time.')
    getGameRegion()
    loadImages()
    initDebugOverlay()
    #cv2.startWindowThread()
    #cv2.namedWindow("debug")
    while True:
        status, msg = win32gui.PeekMessage(hWindow,0,0,win32con.PM_REMOVE)
        if(status):

            win32gui.TranslateMessage(msg)
            win32gui.DispatchMessage(msg)
        else:
            not processInput()
            processScreen()
            mainLogic()
            #cv2.imshow("debug", DEBUG_IMAGE)
    cv2.destroyAllWindows()
        
import win32api, win32con, win32gui, win32ui

def initDebugOverlay():
    global hWindow
    hInstance = win32api.GetModuleHandle()
    className = 'MyWindowClassName'

    # http://msdn.microsoft.com/en-us/library/windows/desktop/ms633576(v=vs.85).aspx
    # win32gui does not support WNDCLASSEX.
    wndClass                = win32gui.WNDCLASS()
    # http://msdn.microsoft.com/en-us/library/windows/desktop/ff729176(v=vs.85).aspx
    wndClass.style          = win32con.CS_HREDRAW | win32con.CS_VREDRAW
    wndClass.lpfnWndProc    = wndProc
    wndClass.hInstance      = hInstance
    wndClass.hCursor        = win32gui.LoadCursor(None, win32con.IDC_ARROW)
    wndClass.hbrBackground  = win32gui.GetStockObject(win32con.WHITE_BRUSH)
    wndClass.lpszClassName  = className
    # win32gui does not support RegisterClassEx
    wndClassAtom = win32gui.RegisterClass(wndClass)

    # http://msdn.microsoft.com/en-us/library/windows/desktop/ff700543(v=vs.85).aspx
    # Consider using: WS_EX_COMPOSITED, WS_EX_LAYERED, WS_EX_NOACTIVATE, WS_EX_TOOLWINDOW, WS_EX_TOPMOST, WS_EX_TRANSPARENT
    # The WS_EX_TRANSPARENT flag makes events (like mouse clicks) fall through the window.
    exStyle = win32con.WS_EX_COMPOSITED | win32con.WS_EX_LAYERED | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT

    # http://msdn.microsoft.com/en-us/library/windows/desktop/ms632600(v=vs.85).aspx
    # Consider using: WS_DISABLED, WS_POPUP, WS_VISIBLE
    style = win32con.WS_DISABLED | win32con.WS_POPUP | win32con.WS_VISIBLE

    #Later come back and ajust size here for non-1080 windows
    # http://msdn.microsoft.com/en-us/library/windows/desktop/ms632680(v=vs.85).aspx
    hWindow = win32gui.CreateWindowEx(
        exStyle,
        wndClassAtom,
        None, # WindowName
        style,
        0, # x
        0, # y
        win32api.GetSystemMetrics(win32con.SM_CXSCREEN), # width
        win32api.GetSystemMetrics(win32con.SM_CYSCREEN), # height
        None, # hWndParent
        None, # hMenu
        hInstance,
        None # lpParam
    )
    # http://msdn.microsoft.com/en-us/library/windows/desktop/ms633540(v=vs.85).aspx
    win32gui.SetLayeredWindowAttributes(hWindow, 0x00ffffff, 255, win32con.LWA_COLORKEY | win32con.LWA_ALPHA)

    # http://msdn.microsoft.com/en-us/library/windows/desktop/dd145167(v=vs.85).aspx
    #win32gui.UpdateWindow(hWindow)

    # http://msdn.microsoft.com/en-us/library/windows/desktop/ms633545(v=vs.85).aspx
    win32gui.SetWindowPos(hWindow, win32con.HWND_TOPMOST, 0, 0, 0, 0,
        win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)

    # http://msdn.microsoft.com/en-us/library/windows/desktop/ms633548(v=vs.85).aspx
    #win32gui.ShowWindow(hWindow, win32con.SW_SHOW)

    #win32gui.PumpWaitingMessages()

def wndProc(hWnd, message, wParam, lParam):
    global hdc
    if message == win32con.WM_PAINT:
        hdc, paintStruct = win32gui.BeginPaint(hWnd)
        debugRender(hWnd,hdc, paintStruct)
        
        win32gui.EndPaint(hWnd, paintStruct)
        return 0

    elif message == win32con.WM_DESTROY:
        print ('Closing the window.')
        win32gui.PostQuitMessage(0)
        return 0

    else:
        return win32gui.DefWindowProc(hWnd, message, wParam, lParam)


def debugRender(hWnd, hdc, paintStruct):
    dpiScale = win32ui.GetDeviceCaps(hdc, win32con.LOGPIXELSX) / 60.0
    fontSize = 12

    # http://msdn.microsoft.com/en-us/library/windows/desktop/dd145037(v=vs.85).aspx
    lf = win32gui.LOGFONT()
    lf.lfFaceName = "Arial"
    lf.lfHeight = int(round(dpiScale * fontSize))
    #lf.lfWeight = 150
    # Use nonantialiased to remove the white edges around the text.
    lf.lfQuality = win32con.NONANTIALIASED_QUALITY
    hf = win32gui.CreateFontIndirect(lf)
    win32gui.SelectObject(hdc, hf)

    rect = win32gui.GetClientRect(hWnd)
    logging.debug(rect)
    # http://msdn.microsoft.com/en-us/library/windows/desktop/dd162498(v=vs.85).aspx
    win32gui.DrawText(
        hdc,
        'Text on the screen',
        -1,
        rect,
        win32con.DT_CENTER | win32con.DT_NOCLIP | win32con.DT_SINGLELINE | win32con.DT_VCENTER
    )

def renderOverlayText(text, region, color ):
    win32gui.SetTextColor(hdc)
    win32gui.DrawText(
        hdc,
        text,
        -1,
        (rect[0]+1,rect[1]+1,rect[2]+1,rect[3]+1),
        win32con.DT_CENTER | win32con.DT_NOCLIP | win32con.DT_SINGLELINE | win32con.DT_VCENTER
    )
    win32gui.DrawText(
        hdc,
        text,
        -1,
        rect,
        win32con.DT_CENTER | win32con.DT_NOCLIP | win32con.DT_SINGLELINE | win32con.DT_VCENTER
    )
   

def loadImages():
    global IMAGES
    global IMAGES_SCALED
    global BUTTONS

    image = cv2.imread('images/finalresults/fr_exit.png',0)
    IMAGES['fr_exit'] = image
    IMAGES_SCALED['fr_exit'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['fr_exit'] = 0

    image = cv2.imread('images/arena/a_status.png',0)
    IMAGES['a_status'] = image
    IMAGES_SCALED['a_status'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])

    image = cv2.imread('images/battle/b_hploc.png',0)
    IMAGES['b_hploc'] = image
    IMAGES_SCALED['b_hploc'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])

    image = cv2.imread('images/battle/b_victory.png',0)
    IMAGES['b_victory'] = image
    IMAGES_SCALED['b_victory'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['b_victory'] = 0

    image = cv2.imread('images/world/w_expmarker.png',0)
    IMAGES['w_expmarker'] = image
    IMAGES_SCALED['w_expmarker'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])

    image = cv2.imread('images/world/w_raid.png',0)
    IMAGES['w_raid'] = image
    IMAGES_SCALED['w_raid'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['w_raid'] = 0

    image = cv2.imread('images/raid/r_lobby.png',0)
    IMAGES['r_lobby'] = image
    IMAGES_SCALED['r_lobby'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])

    image = cv2.imread('images/raid/r_start.png',0)
    IMAGES['r_start'] = image
    IMAGES_SCALED['r_start'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['r_start'] = 0

    image = cv2.imread('images/raid/r_slotopen.png',0)
    IMAGES['r_slotopen'] = image
    IMAGES_SCALED['r_slotopen'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])

    image = cv2.imread('images/battle/h_barend.png',0)
    IMAGES['h_barend'] = image
    IMAGES_SCALED['h_barend'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])

    image = cv2.imread('images/finalresults/fr_loot.png',0)
    IMAGES['fr_loot'] = image
    IMAGES_SCALED['fr_loot'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])

    image = cv2.imread('images/finalresults/fr_abandon.png',0)
    IMAGES['fr_abandon'] = image
    IMAGES_SCALED['fr_abandon'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['b_victory'] = 0

    image = cv2.imread('images/battle/b_error.png',0)
    IMAGES['b_error'] = image
    IMAGES_SCALED['b_error'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['b_error'] = 0

    image = cv2.imread('images/finalresults/fr_claim.png',0)
    IMAGES['fr_claim'] = image
    IMAGES_SCALED['fr_claim'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['fr_claim'] = 0
    
    image = cv2.imread('images/raid/r_lackplayer.png',0)
    IMAGES['r_lackplayer'] = image
    IMAGES_SCALED['r_lackplayer'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['r_lackplayer'] = 0
    
    image = cv2.imread('images/raid/r_lowstamina.png',0)
    IMAGES['r_lowstamina'] = image
    IMAGES_SCALED['r_lowstamina'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['r_lowstamina'] = 0

    image = cv2.imread('images/raid/r_staminapot.png',0)
    IMAGES['r_staminapot'] = image
    IMAGES_SCALED['r_staminapot'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['r_staminapot'] = 0

    image = cv2.imread('images/raidselect/rs_create.png',0)
    IMAGES['rs_create'] = image
    IMAGES_SCALED['rs_create'] = cv2.resize(image, (0,0), fx=GAME_REGION[4], fy=GAME_REGION[4])
    BUTTONS['rs_create'] = 0


def grabWindowImage(windowTitle):

    # Change the line below depending on whether you want the whole window
    # or just the client area. 
    left, top, right, bot = win32gui.GetClientRect(HWND)
    rect = win32gui.GetWindowRect(HWND)

    #left, top, right, bot = win32gui.GetWindowRect(hwnd)
    wWidth = right - left
    wHeight = bot - top

    hwndDC = win32gui.GetWindowDC(HWND)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, wWidth, wHeight)

    saveDC.SelectObject(saveBitMap)

    # Change the line below depending on whether you want the whole window
    # or just the client area. 
    result = windll.user32.PrintWindow(HWND, saveDC.GetSafeHdc(), 1)
    #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    img = np.fromstring(bmpstr, dtype='uint8')
    img.shape = (wHeight,wWidth,4)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(HWND, hwndDC)
    global GAME_REGION
    GAME_REGION = (rect[0], rect[1], wWidth, wHeight, min(wWidth / 1920, wHeight / 1080))

    return cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

def grabWindowPosition(windowTitle):
    hwnd = win32gui.FindWindow(None, windowTitle)

    # Change the line below depending on whether you want the whole window
    # or just the client area. 
    left, top, right, bot = win32gui.GetClientRect(hwnd)
    return (top, left)





def click(x, y):
    adbshell("input tap %s %s" % (x,y), "emulator-5554")
   


def adbshell(command, serial=None, adbpath='adb'):
    args = [adbpath]
    if serial is not None:
        args.extend(['-s', serial])
    args.extend(['shell', command])
    return subprocess.check_output(args)

def pmpath(pname, serial=None, adbpath='adb'):
    return adbshell('pm path {}'.format(pname), serial=serial, adbpath=adbpath)

def getGameRegion():
    """Obtains the region that Kings Raid game is on the screen and assigns it to GAME_REGION. The game must be at the screen with the player at the world map"""
    logging.debug('Finding game region...')

    img = grabWindowImage("Bluestacks")
    height, width, channels = img.shape
    logging.debug('Game region found: %s' % (GAME_REGION,))

   
    #cv2.moveWindow("debug", 1920,0);

def findImage(imagename, area):
    return 

def ScreenCheckBattle(image):
    global DEBUG_IMAGE
    #Landmark
    x,y,w,h = 150,100, 225, 125
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['b_hploc'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['b_hploc'].shape[::-1]
    threshold = 0.8
    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        return True
    return False

def ScreenCheckResults(image):
    global DEBUG_IMAGE
    #Landmark
    x,y,w,h = 1720,875, 1720 + 175, 1720 + 175
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['fr_exit'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['fr_exit'].shape[::-1]
    threshold = 0.8
    
    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['exit'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    return False

def ScreenCheckWorld(image):
    global DEBUG_IMAGE
    #Landmark
    x,y,w,h = 125,50, 200, 100
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['w_expmarker'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['w_expmarker'].shape[::-1]
    threshold = 0.8
    
    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        return True
    return False

def ScreenFindRaidButton(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 1700, 650
    w,h = x + 175, y + 400
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['w_raid'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['w_raid'].shape[::-1]
    threshold = 0.8
    
    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['w_raid'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    return False

def ScreenCheckRaidLobby(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 1300,950
    w,h = x + 150, y + 50
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['r_lobby'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['r_lobby'].shape[::-1]
    threshold = 0.8
    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        return True
    return False

def ScreenCheckRaidSlots(image):
    global DEBUG_IMAGE
    global RAID_OPEN_SLOTS
    #Landmark
    x,y = 1675,720
    w,h = x + 200, y + 190
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['r_slotopen'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['r_slotopen'].shape[::-1]
    threshold = 0.97
    loc = np.where( res >= threshold)
    RAID_OPEN_SLOTS = 0
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        RAID_OPEN_SLOTS = True
        return True
    return False

def ScreenFindHealthEnds(image):
    global DEBUG_IMAGE
    global PLAYER_HEALTHBARS
    del PLAYER_HEALTHBARS[:]
    #Landmark
    x,y = 200,900
    w,h = x + 1700, y + 50
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['h_barend'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['h_barend'].shape[::-1]
    threshold = 0.90
    loc = np.where( res >= threshold)
    count = 0
    for pt in zip(*loc[::-1]):
        PLAYER_HEALTHBARS.append((x + pt[0],y +pt[1]))
        count += 1
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 1)
    return False


def ScreenCheckLoot(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 820,85
    w,h = x + 100, y + 50
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['fr_loot'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['fr_loot'].shape[::-1]
    threshold = 0.8
    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        return True
    return False

def ScreenFindAbandonButton(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 1140, 890
    w,h = x + 95, y + 65
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['fr_abandon'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['fr_abandon'].shape[::-1]
    threshold = 0.8
    
    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['fr_abandon'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    BUTTONS['fr_abandon'] = 0
    return False

def ScreenFindClaimButton(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 1140, 890
    w,h = x + 95, y + 65
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['fr_claim'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['fr_claim'].shape[::-1]
    threshold = 0.8

    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['fr_claim'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    BUTTONS['fr_claim'] = 0
    return False

def ScreenFindRaidStartButton(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 1640, 925
    w,h = x + 110, y + 85
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['r_start'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['r_start'].shape[::-1]
    threshold = 0.8

    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['r_start'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    BUTTONS['r_start'] = 0
    return False

def ScreenFindVictory(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 925, 560
    w,h = x + 75, y + 75
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['b_victory'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['b_victory'].shape[::-1]
    threshold = 0.8

    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['b_victory'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    BUTTONS['b_victory'] = 0
    return False

def ScreenFindBattleError(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 920, 770
    w,h = x + 85, y + 60
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['b_error'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['b_error'].shape[::-1]
    threshold = 0.8

    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['b_error'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    BUTTONS['b_error'] = 0
    return False

def ScreenFindLackPlayersButton(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 920, 770
    w,h = x + 80, y + 60
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['r_lackplayer'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['r_lackplayer'].shape[::-1]
    threshold = 0.8

    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['r_lackplayer'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    BUTTONS['r_lackplayer'] = 0
    return False

def ScreenFindLowStaminaButton(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 920, 805
    w,h = x + 75, y + 55
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['r_lowstamina'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['r_lowstamina'].shape[::-1]
    threshold = 0.8

    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['r_lowstamina'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    BUTTONS['r_lowstamina'] = 0
    return False

def ScreenFindLowStaminaPotButton(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 1100, 850
    w,h = x + 75, y + 55
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['r_staminapot'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['r_staminapot'].shape[::-1]
    threshold = 0.8

    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['r_staminapot'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    BUTTONS['r_staminapot'] = 0
    return False

def ScreenFindCreateRedButton(image):
    global DEBUG_IMAGE
    #Landmark
    x,y = 1480, 405
    w,h = x + 160, y + 55
    #Debug Lines
    cv2.rectangle(DEBUG_IMAGE, (  x,y), (w, h ), (0,0,255), 2)
    checkarea = image[y:h, x:w]
    checkarea_gray = cv2.cvtColor(checkarea, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(checkarea_gray,IMAGES['rs_create'],cv2.TM_CCOEFF_NORMED)
    tw, th = IMAGES['rs_create'].shape[::-1]
    threshold = 0.8

    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(DEBUG_IMAGE, (x + pt[0],y +pt[1]), (x + pt[0] + tw, y + pt[1] + th ), (0,125,255), 2)
        BUTTONS['rs_create'] = (x + pt[0] + int(tw /2), y + pt[1] + int(th /2) )
        return True
    BUTTONS['rs_create'] = 0
    return False

def ScreenIdentifyHeros(image):
    global DEBUG_IMAGE
    global SCREEN
    #Landmark
    return False

def processScreen():
    global DEBUG_IMAGE
    global SCREEN
    global LAST_SCREEN_TIME
    global LASTKNOWNSCREEN
    global LAST_SCREEN_TRANSITION_TIME
    screenimage = grabWindowImage("Bluestacks")
    DEBUG_IMAGE = screenimage.copy()

   
    if ScreenCheckBattle(screenimage):
        if((time.time() - LAST_SCREEN_TRANSITION_TIME) < 3 and len(PLAYER_HEALTHBARS) < 4):
            ScreenFindHealthEnds(screenimage)
        if(len(PLAYER_HEALTHBARS) > 0):
            ScreenIdentifyHeros(screenimage)
        LAST_SCREEN_TIME = time.time()
        if(((time.time() - LAST_SCREEN_TRANSITION_TIME) % 3) < 0.2):
            ScreenFindVictory(screenimage)
            ScreenFindBattleError(screenimage)
            #ScreenFindLoose(screenimage)
        if (SCREEN != Screens.BATTLE):
            LAST_SCREEN_TRANSITION_TIME = time.time()
        SCREEN = Screens.BATTLE
        return
    elif ScreenFindCreateRedButton(screenimage):
        LAST_SCREEN_TIME = time.time()
        if (SCREEN != Screens.RAIDLOBBY):
            LAST_SCREEN_TRANSITION_TIME = time.time()
        SCREEN = Screens.RAIDLIST
        return
    elif ScreenCheckRaidLobby(screenimage):
        ScreenCheckRaidSlots(screenimage)
        ScreenFindRaidStartButton(screenimage)
        ScreenFindLackPlayersButton(screenimage)
        ScreenFindLowStaminaButton(screenimage)
        ScreenFindLowStaminaPotButton(screenimage)
        LAST_SCREEN_TIME = time.time()
        if (SCREEN != Screens.RAIDLOBBY):
            LAST_SCREEN_TRANSITION_TIME = time.time()
        SCREEN = Screens.RAIDLOBBY
        return
    elif ScreenCheckWorld(screenimage):
        ScreenFindRaidButton(screenimage)
        LAST_SCREEN_TIME = time.time()
        if (SCREEN != Screens.WORLD):
            LAST_SCREEN_TRANSITION_TIME = time.time()
        SCREEN = Screens.WORLD
        return
    elif ScreenCheckLoot(screenimage):
        ScreenFindAbandonButton(screenimage)
        ScreenFindClaimButton(screenimage)
        LAST_SCREEN_TIME = time.time()
        if (SCREEN != Screens.WORLD):
            LAST_SCREEN_TRANSITION_TIME = time.time()
        SCREEN = Screens.LOOT
        return
    elif ScreenCheckResults(screenimage):
        LAST_SCREEN_TIME = time.time()
        if (SCREEN != Screens.RESULTS):
            LAST_SCREEN_TRANSITION_TIME = time.time()
        SCREEN = Screens.RESULTS
        return
    if (SCREEN != Screens.NONE):
        LASTKNOWNSCREEN = SCREEN
    if((time.time() -LAST_SCREEN_TIME) > 4):
        SCREEN = Screens.UNKNOWN
    # check if battle screen



#trashy handling of F1-12 keys
def keypress():
    char = None
    if msvcrt.kbhit():
        char = msvcrt.getch()
        if char == b'\x00':
            char = msvcrt.getch()
            logging.debug(char)
    return char

def processInput():
    cv2.waitKey(1)
    global MODE
    char = keypress()
    if char == b';':
        logging.debug("set mode to IDLE")
        MODE = Modes.IDLE
        return True
    elif char == b'<':
        logging.debug("set mode to DRAGON")
        MODE = Modes.DRAGON
        return True
    return True

import msvcrt


def mainLogic():

    global DEBUG_IMAGE
    global LAST_CLICK
    global PLAYER_HEALTHBARS
    global SCREEN
    
    midWidth = int(GAME_REGION[2]/2)
    midHeight = int(GAME_REGION[3]/2)
    textscreen = SCREEN.name
    textmode = MODE.name 
    if SCREEN is Screens.BATTLE:
        cv2.putText(DEBUG_IMAGE,'Detected Heros:' + str(len(PLAYER_HEALTHBARS)),(51,201), FONT, 1,(0,0,0),2,cv2.LINE_AA)
        cv2.putText(DEBUG_IMAGE,'Detected Heros:' + str(len(PLAYER_HEALTHBARS)),(50,200), FONT, 1,(255,125,0),2,cv2.LINE_AA)
        if(BUTTONS['b_victory']):
            if((time.time() - LAST_CLICK) > 2.0 ):
                LAST_CLICK = time.time()
                logging.debug("Victory")
                click(BUTTONS['b_victory'][0],BUTTONS['b_victory'][1])
                LASTKNOWNSCREEN = SCREEN
                SCREEN = Screens.NONE
        if(BUTTONS['b_error']):
            if((time.time() - LAST_CLICK) > 2.0 ):
                LAST_CLICK = time.time()
                logging.debug("An error occured in battle")
                click(BUTTONS['b_error'][0],BUTTONS['b_error'][1])
                LASTKNOWNSCREEN = SCREEN
                SCREEN = Screens.NONE
    elif SCREEN is Screens.RESULTS:
        del PLAYER_HEALTHBARS[:]
        if(MODE == Modes.DRAGON):
            click(BUTTONS['exit'][0],BUTTONS['exit'][1])
            LASTKNOWNSCREEN = SCREEN
            SCREEN = Screens.NONE
    elif SCREEN is Screens.RAIDLIST:
        if(MODE == Modes.DRAGON):
            if((time.time() - LAST_CLICK) > 2.0 ):
                if(BUTTONS['rs_create']):
                    click(BUTTONS['rs_create'][0],BUTTONS['rs_create'][1])

                    for x in range(0, 24):
                        click(740,445)
                    click(950,860)
                    click(180,800)
                    click(340,800)
                    click(500,800)
                    click(340,930)
                    LAST_CLICK = time.time()
                    LASTKNOWNSCREEN = SCREEN
                    SCREEN = Screens.NONE


    elif SCREEN is Screens.RAIDLOBBY:
        if(MODE == Modes.DRAGON):
            cv2.putText(DEBUG_IMAGE,'Raid open slots:' + str(RAID_OPEN_SLOTS),(50,200), FONT, 1,(125,255,255),2,cv2.LINE_AA)
            if (BUTTONS['r_lowstamina']):
                if((time.time() - LAST_CLICK) > 2.0 ):
                    LAST_CLICK = time.time() -1
                    click(BUTTONS['r_lowstamina'][0],BUTTONS['r_lowstamina'][1])
            elif (BUTTONS['r_staminapot']):
                if((time.time() - LAST_CLICK) > 2.0 ):
                    logging.debug("Confirmimg stamina pot usage")
                    LAST_CLICK = time.time() -1
                    click(BUTTONS['r_staminapot'][0],BUTTONS['r_staminapot'][1])
            elif (BUTTONS['r_lackplayer']):
                if((time.time() - LAST_CLICK) > 2.0 ):
                    LAST_CLICK = time.time() -1
                    click(BUTTONS['r_lackplayer'][0],BUTTONS['r_lackplayer'][1])
            if (BUTTONS['r_start']):
                if((time.time() - LAST_CLICK) > 2.0 ):
                    LAST_CLICK = time.time()
                    click(BUTTONS['r_start'][0],BUTTONS['r_start'][1])
                    LASTKNOWNSCREEN = SCREEN
                    SCREEN = Screens.NONE
    elif SCREEN is Screens.WORLD:
        if(MODE == Modes.DRAGON):
            if(BUTTONS['w_raid']):
                click(BUTTONS['w_raid'][0],BUTTONS['w_raid'][1])
                LASTKNOWNSCREEN = SCREEN
                SCREEN = Screens.NONE
    elif SCREEN is Screens.LOOT:
        if (BUTTONS['fr_abandon']):
            if((time.time() - LAST_CLICK) > 2.0 ):
                LAST_CLICK = time.time()
                click(BUTTONS['fr_abandon'][0],BUTTONS['fr_abandon'][1])
                LASTKNOWNSCREEN = SCREEN
                SCREEN = Screens.NONE
        if (BUTTONS['fr_claim']):
            click(BUTTONS['fr_claim'][0],BUTTONS['fr_claim'][1])
            LASTKNOWNSCREEN = SCREEN
            SCREEN = Screens.NONE
    cv2.putText(DEBUG_IMAGE,textscreen,(51,151), FONT, 1,(0,0,0),2,cv2.LINE_AA)
    cv2.putText(DEBUG_IMAGE,textscreen,(50,150), FONT, 1,(255,25,125),2,cv2.LINE_AA)
    cv2.putText(DEBUG_IMAGE,textmode,(51,101), FONT, 1,(0,0,0),2,cv2.LINE_AA)
    cv2.putText(DEBUG_IMAGE,textmode,(50,100), FONT, 1,(0,255,255),2,cv2.LINE_AA)

    return True

    
if __name__ == '__main__':
    main()
