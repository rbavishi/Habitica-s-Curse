""" Module "Config" : Global Config File

    This file contains all the constants used in the program that pertain
    to the configuration of the terminal
"""

# Standard Library imports
import curses
import datetime


NUM_CONTEXT_REGISTERS = 4

# Screen Specifications - Will be adjusted during runtime
SCR_MAX_MENU_ROWS   = 10   # Keep this as an even number please
SCR_X = 0
SCR_Y = 0
SCR_MENU_ITEM_WIDTH = 0
SCR_FIRST_HALF_LENGTH = 0  # Space taken up by the upper half menu of tasks
SCR_TEXT_AREA_LENGTH = 0

# Colors
SCR_COLOR_RED          = 2
SCR_COLOR_GREEN        = 3
SCR_COLOR_YELLOW       = 4
SCR_COLOR_BLUE         = 5
SCR_COLOR_WHITE        = 6
SCR_COLOR_MAGENTA      = 7
SCR_COLOR_CYAN         = 14
SCR_COLOR_LIGHT_ORANGE = 8
SCR_COLOR_DARK_ORANGE  = 9
SCR_COLOR_DARK_GRAY    = 15
SCR_COLOR_LIGHT_GRAY    = 16

# Display Colors with Background
SCR_COLOR_WHITE_GRAY_BGRD = 12
SCR_COLOR_GRAY_WHITE_BGRD = 13

SCR_COLOR_RED_GRAY_BGRD     = 17
SCR_COLOR_GREEN_GRAY_BGRD   = 18
SCR_COLOR_YELLOW_GRAY_BGRD  = 19
SCR_COLOR_BLUE_GRAY_BGRD    = 20
SCR_COLOR_WHITE_GRAY_BGRD   = 21
SCR_COLOR_MAGENTA_GRAY_BGRD = 22

# Background Color (Default black)
SCR_COLOR_BGRD = curses.COLOR_BLACK

# Special Color Codes
SCR_COLOR_NEUTRAL = SCR_COLOR_LIGHT_GRAY

# Special Symbols
SYMBOL_TICK = u'\u2714'.encode("utf-8")
SYMBOL_DISC = u'\u25CF'.encode("utf-8")
SYMBOL_DOWN_TRIANGLE = u'\u25BC'.encode("utf-8")
SYMBOL_UP_TRIANGLE = u'\u25B2'.encode("utf-8")
SYMBOL_DELETE = 'x'
SYMBOL_HEART = u'\u2665'.encode("utf-8")
SYMBOL_EXPERIENCE = u'\u2605'.encode("utf-8")
SYMBOL_GOLD = u'\u25CF'.encode("utf-8")
SYMBOL_MANA = u'\u2600'.encode("utf-8")
SYMBOL_EDIT = u'\u270E'.encode("utf-8")
SYMBOL_LEVEL = u'\u2949'.encode("utf-8")
SYMBOL_DUE = u'\u29D6'.encode("utf-8")

# Status Attributes
HabitStatus = {'+': False, '-': False, SYMBOL_DELETE: False, SYMBOL_EDIT: False}
HabitPosStatus = {'+': False, SYMBOL_DELETE: False, SYMBOL_EDIT: False}
HabitNegStatus = {'-': False, SYMBOL_DELETE: False, SYMBOL_EDIT: False}
TODODailyStatus = {SYMBOL_TICK: False, SYMBOL_DELETE: False, SYMBOL_EDIT: False}
ChecklistStatus = {SYMBOL_TICK: False, SYMBOL_DELETE: False, SYMBOL_EDIT: False}

# Function for setting values at runtime

def ConfigureRuntime(screen):
    global SCR_Y, SCR_X, SCR_MENU_ITEM_WIDTH, SCR_TEXT_AREA_LENGTH, SCR_FIRST_HALF_LENGTH
    SCR_X, SCR_Y = screen.getmaxyx()
    SCR_MENU_ITEM_WIDTH = (SCR_Y - 10)/3
    SCR_TEXT_AREA_LENGTH = (SCR_X - (SCR_MAX_MENU_ROWS + 7 + 4))
    SCR_FIRST_HALF_LENGTH = SCR_MAX_MENU_ROWS + 7

# Parser Settings
SET_COMMANDS = ["d", "due", "every", "weekly", "plus", "minus"]
DIFFS      = ["trivial", "easy", "medium", "hard"]
DATEPARSER = datetime.datetime.strptime 
DATEFORMATS = ["%d/%m/%Y", "%d/%m/%y"]
DEFAULT_REPEAT = {'m': True, 't': True, 'w': True, 'th': True, 'f': True, 's': True, 'su': True}

