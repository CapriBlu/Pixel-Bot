import time

import pyautogui


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


def get_mouse_position():
    return pyautogui.position()


def move_mouse(x, y, duration=0.5):
    pyautogui.moveTo(x, y, duration=duration)


def click_mouse(x, y):
    pyautogui.click(x, y)
