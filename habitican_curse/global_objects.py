""" Module "Global Objects" : Initialization of global objects

    Global objects for screen, interface, user etc. are defined here
"""

screen = None   # Screen Class object
intf = None     # Main Interface
user = None     # User object
reqManager = None
currentTask = None
prevTask = None
content = None  # This will be initialized using a thread,
                # so as to reduce start time

# Task Menus
HabitMenu = None
DailyMenu = None
TODOMenu = None

# Global data
LastUpdate = None
Logger = None
