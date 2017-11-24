
import sys

def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import pip
        pip.main(['install', package])
    finally:
        globals()[package] = importlib.import_module(package)

# Example
if __name__ == '__main__':
    install_and_import('pyautogui')
    install_and_import('matplotlib')
    install_and_import('mss')

print(sys.version)

#!  python3
"""Sushi Go Round Bot
Al Sweigart al@inventwithpython.com @AlSweigart

A bot program to automatically play the Sushi Go Round flash game at http://miniclip.com/games/sushi-go-round/en/
"""

import  time
import os
import logging
import sys
import random
import copy
import cv2
import numpy as np
from matplotlib import pyplot as plt


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d: %(message)s', datefmt='%H:%M:%S')
#logging.disable(logging.DEBUG) # uncomment to block debug log messages


# Global variables
GAME_REGION = () # (left, top, width, height) values coordinates of the game window
SCREEN = () # Active Screen

class Hero:
    def __init__(self, name, facemark, skills):
        self.name = name
        self.facemark = facemark
        self.skills = skills













def main():
    """Runs the entire program. The Kings Raid Program must be visible on the screen with the player at the world map"""
    logging.debug('Program Started. Press Ctrl-C to abort at any time.')
    logging.debug('To interrupt mouse movement, move mouse to upper left corner.')
    getGameRegion()

def imPath(filename):
    """A shortcut for joining the 'images/'' file path, since it is used so often. Returns the filename with 'images/' prepended."""
    return os.path.join('images', filename)


def screen_record_efficient():
    # 800x600 windowed mode
    mon = {'top': 40, 'left': 0, 'width': 800, 'height': 640}

    title = '[MSS] FPS benchmark'
    fps = 0
    sct = mss.mss()
    last_time = time.time()

    while time.time() - last_time < 15:
        img = numpy.asarray(sct.grab(mon))
        fps += 1

        cv2.imshow(title, img)
        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break

    return (fps / (time.time() - last_time))








def getGameRegion():
    """Obtains the region that Kings Raid game is on the screen and assigns it to GAME_REGION. The game must be at the screen with the player at the world map"""
    global GAME_REGION
    


    # identify the top-left corner
    logging.debug('Finding game region...')
    mon = -1;
    template = cv2.imread('images/K_doubleslash.png',0)
    w, h = template.shape[::-1]
    sct = mss.mss()
    monitor = {'top': 40, 'left': 0, 'width': 800, 'height': 640}
    while GAME_REGION is None:
        screencap = np.asarray(sct.grab(sct.monitors[0]), dtype='uint8')
        img_rgb = screencap.copy()
        logging.debug(img_rgb.dtype)

        img_gray = cv2.cvtColor(screencap, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where( res >= threshold)
        for pt in zip(*loc[::-1]):
            cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0,0,255), 2)

        cv2.imwrite('res.png',img_rgb)
        cv2.startWindowThread()
        cv2.namedWindow("preview")
        cv2.imshow("preview", img_rgb)
        

    #if region is None:
    #    raise Exception('Could not find game on screen. Is the game visible?')
    
    ## calculate the region of the entire game
    #logging.debug(region)
    #topRightX = region[0] + region[2] # left + width
    #topRightY = region[1] # top
    #GAME_REGION = (topRightX - 640, topRightY, 640, 480) # the game screen is always 640 x 480
    #logging.debug('Game region found: %s' % (GAME_REGION,))



main()