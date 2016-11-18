""" Module "Interface" : Main Interface

    Command parsing, menu positioning etc.
"""
# Standard Library Imports
import curses
import shlex # For parsing

# Custom Module Imports
import config as C
from screen import Screen
import global_objects as G
import helper as H
import menu as M
import debug as DEBUG
import content as CT

#Set up logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug logging started for %s..." % __name__)

def Idx(parsed, index):
    # Return element in the parsed list at index. Return "" if not present
    try:
        return parsed[index]
    except:
        return ""


class Interface(object):

    def __init__(self):
        self.trinity = []
        self.currentMenu = 0

    def Init(self):
        G.HabitMenu.SetXY(1, 2)
        G.DailyMenu.SetXY(1, 6 + C.SCR_MENU_ITEM_WIDTH)
        G.TODOMenu.SetXY(1, 10 + 2*C.SCR_MENU_ITEM_WIDTH)

        G.HabitMenu.Reload()
        G.DailyMenu.Reload()
        G.TODOMenu.Reload()

        G.HabitMenu.Init()
        G.DailyMenu.Init()
        G.TODOMenu.Init()

        # Borders
        G.screen.Display(u'\u2550'.encode('utf-8')*C.SCR_Y, 14, 0,bold=True,color=C.SCR_COLOR_WHITE)

        # User Stats
        G.user.PrintData()

        # Save this context for future use in a register
        G.screen.SaveInRegister(0)
        G.screen.SaveInRegister(3) # For storing marks and deletes

        # Used for scrolling
        self.trinity = [G.HabitMenu, G.DailyMenu, G.TODOMenu]
        self.currentMenu = 0
        for i in xrange(0, 3):
            if not self.trinity[i].IsEmpty():
                self.currentMenu = i
                break
        self.trinity[self.currentMenu].InitialCurrentTask()
        self.Highlight()

    def Highlight(self):
        if G.prevTask != None:
            G.prevTask.DisplayName()

        G.currentTask.HighlightName()

    def ScrollUp(self):
        self.trinity[self.currentMenu].ScrollUp()
        self.Highlight()

    def ScrollDown(self):
        self.trinity[self.currentMenu].ScrollDown()
        self.Highlight()

    def ScrollLeft(self):
        if self.currentMenu == 0: # Very Annoying otherwise
            return

        for i in [(self.currentMenu-1)%3, (self.currentMenu-2)%3,
                self.currentMenu]:
            if not self.trinity[i].IsEmpty():
                break
        self.currentMenu = i
        self.trinity[self.currentMenu].InitialCurrentTask()
        self.Highlight()

    def ScrollRight(self):
        if self.currentMenu == 2: # Very annoying otherwise
            return
        for i in [(self.currentMenu+1)%3, (self.currentMenu+2)%3,
                self.currentMenu]:
            if not self.trinity[i].IsEmpty():
                break
        self.currentMenu = i
        self.trinity[self.currentMenu].InitialCurrentTask()
        self.Highlight()

    # For marking habits as "+"
    def ToggleMarkUp(self):
        if self.currentMenu != 0:
            return

        G.currentTask.ToggleMarkUp()
        G.currentTask.HighlightName()

    # For marking habits as "-"
    def ToggleMarkDown(self):
        if self.currentMenu != 0:
            return

        G.currentTask.ToggleMarkDown()
        G.currentTask.HighlightName()

    # For marking tasks and dailies as completed
    def ToggleMark(self):
        if self.currentMenu == 0:
            return

        G.currentTask.ToggleMark()
        G.currentTask.HighlightName()

    # For marking tasks for deletion
    def ToggleDelete(self):

        G.currentTask.ToggleDelete()
        G.currentTask.HighlightName()

    # Display Checklist
    def Checklist(self):
        G.screen.SaveInRegister(1)
        G.currentTask.ShowChecklist()
        G.screen.RestoreRegister(1)
        self.Highlight()

    # Write out any unsaed changes
    def FlushChangesToQueue(self):
        G.prevTask = None
        G.currentTask = None

        G.HabitMenu.WriteChanges()
        G.DailyMenu.WriteChanges()
        G.TODOMenu.WriteChanges()

    # Command Parser
    def Parser(self, command):
        parsed = shlex.split(command)
        if Idx(parsed, 0) == "set":


            if not Idx(parsed, 1) in  C.SET_COMMANDS:
                DEBUG.Display("Invalid Set: " + command)
                return
            c = Idx(parsed, 1)

            # Change Difficulty
            if c == "d":
                if (not Idx(parsed, 2) in C.DIFFS) or (Idx(parsed, 3) != "") :
                    DEBUG.Display("Invalid set d: " + Idx(parsed, 2))
                    return
                key = Idx(parsed, 2)
                G.currentTask.ChangePriority(key)
                self.Highlight()
                return

            # Change/Remove Due Date
            elif c == "due":
                if G.currentTask.task_type != "todo":
                    return
                # set due remove - Remove the current due date if any
                if Idx(parsed, 2) == "remove" or Idx(parsed, 2) == "delete":
                    G.currentTask.RemoveDueDate()
                    self.Highlight()
                    return

                retDate = H.DatePicker()
                if retDate != None:
                    G.currentTask.ChangeDueDate(retDate.ConvertUTC())

                self.Highlight()
                return

            # Set weekly options for dailies
            elif c == "weekly":
                if G.currentTask.task_type != "daily":
                    return

                repeat = H.RepeatPicker(G.currentTask.task.repeat)
                if repeat != None:
                    G.currentTask.SetWeekly(repeat)
                self.Highlight()
                return

            # Set every X days option for dailies
            elif c == "every":
                if G.currentTask.task_type != "daily":
                    return

                if not Idx(parsed, 2).isdigit():
                    DEBUG.Display("Invalid number of days.")
                    return

                G.currentTask.SetEvery(int(Idx(parsed, 2)))
                self.Highlight()
                return

        elif Idx(parsed, 0) == "et": # Create Todo

            c_title = Idx(parsed, 1)
            if c_title == "" :
                title = H.TitlePicker()
            else:
                title = Idx(parsed, 1)

            G.reqManager.CreateTask_orig(title, "todo")
            self.trinity[self.currentMenu].InitialCurrentTask()

            self.Highlight()
            return

        elif Idx(parsed, 0) == "ed": # Create Daily

            c_title = Idx(parsed, 1)
            if c_title == "" :
                title = H.TitlePicker()
            else:
                title = Idx(parsed, 1)

            G.reqManager.CreateTask_orig(title, "daily")
            self.trinity[self.currentMenu].InitialCurrentTask()
            self.Highlight()
            return

        elif Idx(parsed, 0) == "eh": # Create Habit

            c_title = Idx(parsed, 1)
            if c_title == "" :
                title = H.TitlePicker()
            else:
                title = Idx(parsed, 1)

            G.reqManager.CreateTask_orig(title, "habit")
            self.trinity[self.currentMenu].InitialCurrentTask()
            self.Highlight()
            return

        if command != "":
            DEBUG.Display("Invalid: " + command)


    def Command(self, command):
        if command == "w":
            self.FlushChangesToQueue() #Write out things to the request queue
            G.reqManager.Flush() #Send the queue

        elif command == "r":
            G.prevTask = None
            G.currentTask = None
            self.FlushChangesToQueue() #Write out things to the request queue
            G.reqManager.Flush() #Send the queue

            G.reqManager.FetchData()
            G.screen.Erase()
            self.Init()

            # User Stats
            while (G.content == None):
                DEBUG.Display("Fetching Content...")
                time.sleep(5)
            DEBUG.Display(" ")

            G.user.attrStats = H.GetUserStats(G.user.data)

            G.user.PrintUserStats()

        elif command == "party":
            G.screen.SaveInRegister(1)
            G.user.GetPartyData()
            G.screen.RestoreRegister(1)

        elif command == "data-display":
            CT.GetData()

        elif command == "help":
            H.HelpPage()

        else:
            self.Parser(command)

    def Input(self):
        while(1):
            try:
                # Don't starve the book-keeping thread unnecessarily
                G.screen.Release()
            except:
                pass

            c = G.screen.GetCharacter()

            # Clear Notification Line
            DEBUG.Display(" ")

            if c == curses.KEY_UP or c == ord('k'):
                self.ScrollUp()
            elif c == curses.KEY_DOWN or c == ord('j'):
                self.ScrollDown()
            elif c == curses.KEY_LEFT or c == ord('h'):
                self.ScrollLeft()
            elif c == curses.KEY_RIGHT or c == ord('l'):
                self.ScrollRight()
            elif c == ord('m'):
                self.ToggleMark()
            elif c == ord('d'):
                self.ToggleDelete()
            elif c == ord('+'):
                self.ToggleMarkUp()
            elif c == ord('-'):
                self.ToggleMarkDown()
            elif c == ord('c'):
                self.Checklist()
            elif c == ord(':'):
                command = G.screen.Command()

                # Vim style exit
                if command == "q!":
                    break

                if command == "wq":
                    self.FlushChangesToQueue() #Write out things to the request queue
                    G.reqManager.Flush() #Send the queue
                    break

                if command == "q":
                    self.FlushChangesToQueue()

                    if(len(G.reqManager.MarkUpQueue) |
                       len(G.reqManager.MarkDownQueue) |
                       len(G.reqManager.MarkQueue) |
                       len(G.reqManager.DeleteQueue) |
                       len(G.reqManager.EditQueue) ):
                        DEBUG.Display("No write since last change (add ! to override)")
                        continue #Restart command loop
                    break #exit

                G.screen.Display(" "*(C.SCR_Y-1), C.SCR_X-1, 0)
                self.Command(command)
