""" Module "Task" : Classes for storing task information

    The python class version of the model described on the github page of
    Habitica.
"""
# Standard Library Imports
import textwrap
import uuid

# Custom Module Imports

import config as C
from screen import Screen
import global_objects as G
import helper as H
import menu as M
import debug as DEBUG

#Set up logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug logging started for %s..." % __name__)

def ValueToColor(value):
    if value < -20:
        return C.SCR_COLOR_RED
    elif value < -10:
        return C.SCR_COLOR_DARK_ORANGE
    elif value < -1:
        return C.SCR_COLOR_LIGHT_ORANGE
    elif value < 1:
        return C.SCR_COLOR_YELLOW
    elif value < 5:
        return C.SCR_COLOR_GREEN
    elif value < 20:
        return C.SCR_COLOR_CYAN
    else:
        return C.SCR_COLOR_BLUE


def PriorityToDifficulty(priority):
    if priority == 0.1:
        return "trivial"
    elif priority == 1:
        return "easy"
    elif priority == 1.5:
        return "medium"
    else:
        return "hard"

def RepeatToString(repeat):
    Translate = {'m': 'Mon', 't': 'Tue', 'th': 'Thurs', 'w': 'Wed', 's':'Sat', 'su': 'Sun', 'f': 'Fri'}
    TranslateOrder = ['m', 't', 'w', 'th', 'f', 's', 'su']
    retString = ""
    for i in TranslateOrder:
        if repeat[i]:
            retString += Translate[i] + " "

    return retString

def ChecklistMenu(checklist):
    #if not checklist:
        #return None

    checklist_items = []
    for i in checklist:
        task_item = ChecklistItem(i)
        checklist_items += [M.MenuItem(task_item, 'checklist', task_item.text, width=(C.SCR_Y-20))]

    menuObj = M.Menu(checklist_items, 'Checklist', (C.SCR_X - (C.SCR_MAX_MENU_ROWS+7+4+2)), 'checklist_menu')
    menuObj.SetXY(C.SCR_MAX_MENU_ROWS+7, 5)
    return menuObj

def DummyChecklistItem():
    # Return an "Add an item"-named dummy checklist item
    newItem = {}
    newItem[u'text']      = u'Add New Item'
    newItem[u'completed'] = False
    newItem[u'id']        = str(uuid.uuid4())
    return M.MenuItem(ChecklistItem(newItem), 'checklist', newItem['text'], width=(C.SCR_Y-20))


class Task(object):
    """ Basic template for a task. There will be separate derived classes for
    Habits, TODOs and Dailies. Basic display facilities are described in the
    display function of this class. Other details are displayed by the
    function in the derived classes
    """

    def __init__(self, data):
        self.data = data          # JSON response

        # Basic Details
        self.text        = data['text'].encode("utf-8")
        self.taskID      = data['id']
        self.dateCreated = H.DateTime(str(data['createdAt']))
        self.priority    = data['priority']
        self.value       = data['value']

        # Derived Details
        self.color       = ValueToColor(self.value)
        self.difficulty  = PriorityToDifficulty(self.priority)

        # Coordinates for displaying complete details
        self.x           = 0
        self.y           = 0

    def SetXY(self, x=0, y=0):
        self.x = x
        self.y = y

    def Display(self):
        #G.screen.RestoreRegister(0)
        G.screen.ClearTextArea()
        X, Y = self.x, self.y

        # Title Display
        title_wrap = textwrap.wrap(self.text, C.SCR_Y-20)
        for i in title_wrap:
            G.screen.Display(i+'\n',  X, Y,
                    color=self.color,bold=True)
            X += 1

        # Difficulty
        G.screen.Display("Difficulty: ", X, Y,bold=True)
        G.screen.Display(self.difficulty, X, Y+12,
                color=C.SCR_COLOR_MAGENTA, bold=True)
        X += 1

        # Date Created
        G.screen.Display("Date Created: ", X, Y,bold=True)
        G.screen.Display(self.dateCreated.DateCreatedFormat(),X, Y+14,
                         color=C.SCR_COLOR_MAGENTA,bold=True)
        X += 1

        return X

    def ChangePriority(self, key):
        priorityDict = {"trivial": 0.1, "easy": 1, "medium": 1.5, "hard": 2}
        self.priority = priorityDict[key]
        self.data['priority'] = self.priority
        self.difficulty = key


class ChecklistItem(object):
    """ Class for holding a checklist item """

    def __init__(self, data):

        # Checklist Item Specifications
        self.data      = data
        self.text      = data['text'].encode("utf-8")
        self.completed = data['completed']
        self.ID        = data['id']
        self.newName   = ""               # In case we change the name

    def Display(self): # Dummy
        return

    def Mark(self):
        self.completed ^= True
        self.data['completed'] = self.completed

    def ChangeName(self):
        self.text = self.newName
        self.data['text'] = self.text


class Habit(Task):
    """ Class for holding a habit """

    def __init__(self, data):
        super(Habit, self).__init__(data)
        self.task_type = "habit"

        # Special Attributes
        self.up   = data['up']
        self.down = data['down']

    def Display(self):
        X = super(Habit, self).Display()
        Y = self.y

        # Something can be added here
        # Maybe use the data-display tool

    def ShowChecklist(self, menuItem):
        # Dummy to avoid crashes
        return

class Daily(Task):
    """ Class for holding a daily """

    def __init__(self, data):
        self.task_type = "daily"
        super(Daily, self).__init__(data)

        # Special Attributes
        self.completed = data['completed']
        self.checklist = data['checklist']

        self.frequency = data['frequency']
        self.repeat    = data['repeat']
        self.everyX    = data['everyX']
        self.startDate = str(data['startDate'])

        # Is it due today?
        self.isDue     = H.isDueDaily(self.data)
        if not self.isDue:
            self.color = C.SCR_COLOR_NEUTRAL


        # Checklist Menu. None if it is empty
        self.checklistMenu = ChecklistMenu(self.checklist)

    def ChecklistTuple(self):  # Return (done/total)
        done = len([i for i in self.checklist if i['completed']])
        total = len(self.checklist)
        return [done, total]

    def Display(self):
        X = super(Daily, self).Display()
        Y = self.y

        if self.frequency == "daily": # Every X days
            G.screen.Display("Every " + str(self.everyX) + " days",X, Y,
                    color=C.SCR_COLOR_MAGENTA, bold=True)
        else:                         # Active on some days of the week
            G.screen.Display("Active: " + RepeatToString(self.repeat), X, Y,
                    color=C.SCR_COLOR_MAGENTA, bold=True)
        X += 2

        # Checklist
        if self.checklist:
            done, total = self.ChecklistTuple()
            G.screen.Display("Checklist: " + "("+str(done)+"/"+str(total)+")" + " completed", X, Y,
                             color=C.SCR_COLOR_MAGENTA,bold=True)
            X += 2

        if not self.isDue:
            G.screen.Display("Not Due Today", X, Y,color=C.SCR_COLOR_NEUTRAL, bold=True)

    def ShowChecklist(self, menuItem):
        if self.checklistMenu == None:
            return

        G.screen.ClearTextArea()
        self.checklistMenu.Init()
        retVal = self.checklistMenu.Input()

        if retVal == 0: # Cancel changes
            self.checklistMenu.CancelChecklistChanges()
        else:
            self.checklistMenu.WriteChecklistChanges(menuItem)

    def ChangeChecklist(self, checklist):
        self.checklist = checklist
        self.data['checklist'] = checklist

    def SetWeekly(self, repeat):
        if self.frequency != "weekly":
            self.frequency = "weekly"
            self.data['frequency'] = self.frequency
            self.data['everyX'] = 1
            self.everyX = 1

        self.repeat = repeat
        self.data['repeat'] = repeat

        # Is it due today?
        self.isDue     = H.isDueDaily(self.data)
        if not self.isDue:
            self.color = C.SCR_COLOR_NEUTRAL
        else:
            self.color = ValueToColor(self.priority)

    def SetEvery(self, days):
        if self.frequency != "daily":
            self.frequency = "daily"
            self.data['frequency'] = self.frequency
            self.repeat = C.DEFAULT_REPEAT
            self.data['repeat'] = self.repeat

        self.everyX = days
        self.data['everyX'] = days

        # Is it due today?
        self.isDue     = H.isDueDaily(self.data)
        if not self.isDue:
            self.color = C.SCR_COLOR_NEUTRAL
        else:
            self.color = ValueToColor(self.priority)


class TODO(Task):
    """ Class for holding a habit """

    def __init__(self, data):
        self.task_type = "todo"
        super(TODO, self).__init__(data)

        # Special Attributes
        self.completed = data['completed']
        self.checklist = data['checklist']

        if data.has_key('date') and data['date'] != "" and data['date'] != None: # Due Date Stuff
            self.dueDate = H.DateTime(str(data['date'])).DueDateFormat()
            self.date    = str(data['date'])
        else:
            self.dueDate = ""
            self.date    = ""

        # Checklist Menu. None if it is empty
        self.checklistMenu = ChecklistMenu(self.checklist)

    def ChecklistTuple(self):  # Return (done/total)
        done = len([i for i in self.checklist if i['completed']])
        total = len(self.checklist)
        return [done, total]

    def ChangeDueDate(self, date):
        self.data['date'] = date
        self.dueDate = H.DateTime(str(self.data['date'])).DueDateFormat()
        self.date = str(self.data['date'])

    def RemoveDueDate(self):
        if self.data.has_key('date'):
            self.data['date'] = ""
        else:
            logger.warn('Trying to delete due date from task without one!')

        self.dueDate = ""
        self.date    = ""

    def Display(self):
        X = super(TODO, self).Display()
        Y = self.y

        # Due Date
        if self.date != "":
            G.screen.Display("Due: " + H.DateTime(self.date).DateCreatedFormat() + " (dd/mm/yy)",
                             X,Y,color=C.SCR_COLOR_MAGENTA, bold=True)
            X += 2

        # Checklist
        if self.checklist:
            done, total = self.ChecklistTuple()
            G.screen.Display("Checklist: " + "("+str(done)+"/"+str(total)+")" + " completed",
                             X,Y,color=C.SCR_COLOR_MAGENTA, bold=True)
            X += 2

    def ShowChecklist(self, menuItem):
        if self.checklistMenu == None:
            return

        G.screen.ClearTextArea()
        self.checklistMenu.Init()
        retVal = self.checklistMenu.Input()

        if retVal == 0: # Cancel changes
            self.checklistMenu.CancelChecklistChanges()
        else:
            self.checklistMenu.WriteChecklistChanges(menuItem)

    def ChangeChecklist(self, checklist):
        self.checklist = checklist
        self.data['checklist'] = checklist
