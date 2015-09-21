""" Module "Request Manager" : Module for interacting via Habitica API

    All fetching, scoring, editing, deleting activities are defined here.
"""
# Standard Library Imports
import requests
import os
import time

# Custom Module Imports

import config as C
from screen import Screen
import global_objects as G
import helper as H
import menu as M
import task as T
import debug as DEBUG
import user as U

# URL Definitions
GET_TASKS_URL = "https://habitica.com:443/api/v2/user/tasks"
GET_USER_URL  = "https://habitica.com:443/api/v2/user/"


class RequestManager(object):
    """ The main class for sending/receiving data to the habitica server """

    def __init__(self):
        f = open(os.getenv("HOME")+'/.habiticarc', 'r')
        self.userID  = f.readline()[:-1]
        self.key     = f.readline()[:-1]
        self.headers = {'x-api-key': self.key, 'x-api-user': self.userID}

        # Flush Queues
        self.MarkUpQueue = []
        self.MarkDownQueue = []
        self.MarkQueue = []
        self.DeleteQueue = []
        self.EditQueue = []

    def FetchData(self):
        del(G.HabitMenu)
        del(G.TODOMenu)
        del(G.DailyMenu)

        DEBUG.Display("Connecting...")
        response = requests.get(GET_USER_URL, headers=self.headers)
        DEBUG.Display("Connected")
        time.sleep(1)
        DEBUG.Display(" ")

        # Need some exception definitions or failure indicators here
        if(response.status_code!=200):
            return 

        json = response.json()
        habits, dailies, todos = json['habits'], json['dailys'], json['todos']

        # Initialize User Stats
        G.user = U.User(json['stats']) 

        # Convert everything to list form. In case of a single task, the
        # response won't be a list
        habits = ([habits]) if type(habits)!=list else habits
        dailies = ([dailies]) if type(dailies)!=list else dailies
        todos = ([todos]) if type(todos)!=list else todos

        # These will contain the menu items passed to create the Habit, Daily
        # and Todo menus
        habit_items = []
        dailies_items = []
        todos_items = []

        for i in habits:
            item = T.Habit(i)
            habit_items += [M.MenuItem(item, "habit", item.text)]

        for i in dailies:
            item = T.Daily(i)
            dailies_items += [M.MenuItem(item, "daily", item.text)]

        for i in todos:
            if i['completed']:
                continue
            item = T.TODO(i)
            todos_items += [M.MenuItem(item, "todo", item.text)]

        G.HabitMenu = M.Menu(habit_items, "Habits")
        G.DailyMenu = M.Menu(dailies_items, "Dailies")
        G.TODOMenu  = M.Menu(todos_items, "TODOs")

    def Flush(self):
        DEBUG.Display("Please Wait...")

        # Difference obtained in user stats due to these operations
        diffDict = {'hp': 0, 'gp': 0, 'mp': 0, 'exp': 0, 'lvl': 0}
        origDict = {'hp': G.user.hp, 'gp': G.user.gp, 'mp': G.user.mp,
                    'exp': G.user.exp, 'lvl': G.user.lvl}

        # Habits marked as +
        for i in self.MarkUpQueue:
            URL = GET_TASKS_URL + "/" + i.task.taskID + "/" + "up"
            response = requests.post(URL, headers=self.headers)

            # Need some error handling here
            if response.status_code!=200:
                return

            json = response.json()
            for i in diffDict:
                diffDict[i] = json[i] - origDict[i]

        # Habits marked as -
        for i in self.MarkDownQueue:
            URL = GET_TASKS_URL + "/" + i.task.taskID + "/" + "down"
            response = requests.post(URL, headers=self.headers)

            # Need some error handling here
            if response.status_code!=200:
                return

            json = response.json()
            for i in diffDict:
                diffDict[i] = json[i] - origDict[i]

        # Dailies and TODOS marked as completed
        for i in self.MarkQueue:
            if i.task.task_type != "daily" or (not i.task.completed):
                URL = GET_TASKS_URL + "/" + i.task.taskID + "/" + "up"
            else:
                URL = GET_TASKS_URL + "/" + i.task.taskID + "/" + "down"
            response = requests.post(URL, headers=self.headers)

            # Need some error handling here
            if response.status_code!=200:
                return

            if i.task.task_type == "todo":
                G.TODOMenu.Remove(i.task.taskID)
            elif i.task.task_type == "daily":
                i.task.completed ^= True

            json = response.json()
            for i in diffDict:
                diffDict[i] = json[i] - origDict[i]

        for i in self.DeleteQueue:
            URL = GET_TASKS_URL + "/" + i.task.taskID
            response = requests.delete(URL, headers=self.headers)

            # Need some error handling here
            if response.status_code!=200:
                return

            if i.task.task_type == "habit":
                G.HabitMenu.Remove(i.task.taskID)
            elif i.task.task_type == "daily":
                G.DailyMenu.Remove(i.task.taskID)
            elif i.task.task_type == "todo":
                G.TODOMenu.Remove(i.task.taskID)

        G.screen.Erase()
        G.user.PrintDiff(diffDict)
        G.intf.Init()


