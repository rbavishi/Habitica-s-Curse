""" Module "Request Manager" : Module for interacting via Habitica API

    All fetching, scoring, editing, deleting activities are defined here.
"""
# Standard Library Imports
import requests
import time
import imp
import importlib
import datetime

# Custom Module Imports

import config as C
from screen import Screen
import global_objects as G
import helper as H
import menu as M
import task as T
import debug as DEBUG
import user as U

#Set up logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug logging started for %s..." % __name__)

# URL Definitions
API_URL = "https://habitica.com:443/api/v3"

#Request Methods
request_methods = dict()
request_methods['get'] = requests.get
request_methods['put'] = requests.put
request_methods['post'] = requests.post
request_methods['delete'] = requests.delete


class RequestManager(object):
    """ The main class for sending/receiving data to the habitica server """

    def __init__(self):

        self.headers = {'x-api-key': C.getConfig("key"), 'x-api-user': C.getConfig("uuid")}
        self.ClearQueues()


    # General Wrapper to fetch JSON data from server
    def APIV3_call(self,path,params={},failure='hard',method='get',obj=None):

        if method not in request_methods:
            raise ValueError("Unknown Method type ",method)

        url = API_URL+"/"+path

        if(method == 'get'):
            url+="?"
            for param, value in params.iteritems():
                url+=param + "=" + value

        logger.warn("Calling V3 API: %s" % url)
        resp = request_methods[method](url, headers=self.headers,json=obj)

        # Need some error handling here
        if resp.status_code == 200:
            logger.debug("HTTP Response: 200 Okay!")
            rval = resp.json()['data']
        elif  resp.status_code == 201:
            logger.debug("HTTP Response: 201 Object Created")
            rval = resp.json()['data']
        else:
            if(failure=='hard'):
                raise ValueError("HTTP Response not recognized: %d" % resp.status_code)
            else:
                logger.warn("HTTP Response not recognized: %d" % resp.status_code)
                rval = -1

        return rval

    ################################
    ## V3 API Calls                #
    ################################

    #Fetches the 'content', which is basically all the strings and values that are constant in the game
    # https://habitica.com/apidoc/#api-Content-ContentGet
    def FetchGameContent(self):
        return self.APIV3_call("content")

    #Fetches the User Object from the API
    # https://habitica.com/apidoc/#api-User-UserGet
    def FetchUserData(self):
        return self.APIV3_call("user")

    #Fetches User Tasks from the API.
    # https://habitica.com/apidoc/#api-Task-GetUserTasks
    # task_type can be "habits", "dailys", "todos", "rewards", "completedTodos"
    def FetchUserTasks(self,task_type=None):
        tasks = None
        if(task_type is None):
            tasks = self.APIV3_call("tasks/user")
        else:
            if(task_type not in ["habits", "dailys", "todos", "rewards", "completedTodos"]):
                raise ValueError("Unknown task type %s" % task_type)
            tasks = self.APIV3_call("tasks/user",{'type':task_type})

        return tasks

    # Score a task up/down
    # https://habitica.com/apidoc/#api-Task-ScoreTask
    def ScoreTask(self,task_id,direction):
        if(direction not in ['up','down']):
            raise ValueError("Unknown task direction %s" % direction)
        return self.APIV3_call("tasks/"+task_id+"/score/"+direction,method='post')

    # Add a new task
    # https://habitica.com/apidoc/#api-Task-CreateUserTasks
    def CreateTask(self, task_obj):
        return self.APIV3_call("tasks/user",method='post',obj=task_obj)

    # Delete a task
    # https://habitica.com/apidoc/#api-Task-DeleteTask
    def DeleteTask(self, task_id):
        return self.APIV3_call("tasks/"+task_id,method='delete')

    # Update a task
    # https://habitica.com/apidoc/#api-Task-UpdateTask
    def UpdateTask(self, task_id, task_obj):
        return self.APIV3_call("tasks/"+task_id,method='put',obj=task_obj)

    #Fetches the User Object from the API
    # https://habitica.com/apidoc/#api-Group-GetGroup
    def FetchParty(self):
        return self.APIV3_call("groups/party")



    ################################
    ## Deprecated Functions        #
    ################################

    # These are functions that don't really belong in the
    # request manager (they're interface/model based, not
    # request based

    def CreateTask_orig(self,title,task_type):
        task = {}
        task['text'] = title.decode("utf-8")
        task['type'] = task_type
        task['priority'] = 1

        if task_type == 'todo' or task_type == 'daily':
            task['checklist'] = []
        if task_type == "daily":
            task['everyX'] = 1
            task['frequency'] = 'weekly'
            task['repeat'] = {'m': True, 't': True, 'w': True, 'th': True, 'f': True, 's': True, 'su': True}
        if task_type == "habit":
            task['up'] = True
            task['down'] = True


        DEBUG.Display("Creating Task...");
        ret_task = self.CreateTask(task)
        DEBUG.Display(" ")

        logger.debug(ret_task)

        if task_type == "habit":
            item = T.Habit(ret_task)
            menu_item = M.MenuItem(item, "habit", item.text)
            G.HabitMenu.Insert(menu_item)

        elif task_type == "daily":
            item = T.Daily(ret_task)
            menu_item = M.MenuItem(item, "daily", item.text)
            G.DailyMenu.Insert(menu_item)

        elif task_type == "todo":
            item = T.TODO(ret_task)
            menu_item = M.MenuItem(item, "todo", item.text)
            G.TODOMenu.Insert(menu_item)

    # Flush Queues (this doesn't belong as part of the reuqest manager!)
    def ClearQueues(self):

        self.MarkUpQueue = []
        self.MarkDownQueue = []
        self.MarkQueue = []
        self.DeleteQueue = []
        self.EditQueue = []

    #Fetches basic user data for the interface
    def FetchData(self):


        G.LastUpdate = datetime.datetime.now()

        #Get the user data from the API
        DEBUG.Display("Connecting...")

        user_json = self.FetchUserData()
        task_json = self.FetchUserTasks()

        DEBUG.Display("Connected")
        time.sleep(1)
        DEBUG.Display(" ")


        # Initialize User Stats
        G.user = U.User( user_json )

        # These will contain the menu items passed to create the Habit, Daily
        # and Todo menus
        habit_items   = []
        dailies_items = []
        todos_items   = []

        logger.debug("Found %d tasks" % len(task_json))

        for i in task_json:
            logger.debug("Processing a TODO: %s" % str(i['text']))
            if( i['type'] == "habit" ):
                item = T.Habit(i)
                habit_items += [M.MenuItem(item, "habit", item.text)]
            elif( i['type'] == "daily" ):
                item = T.Daily(i)
                dailies_items += [M.MenuItem(item, "daily", item.text)]
            elif( i['type'] == "todo" ):
                if i['completed']:
                    continue
                item = T.TODO(i)
                todos_items += [M.MenuItem(item, "todo", item.text)]
            elif( i['type'] == "reward" ):
                logger.warn("Custom Rewards aren't implemented yet, but the user has one: %s" % i['text'])
            else:
                logger.debug("Weird task type: %s" % str(i))
                raise ValueError("Unknown task type %s" % i['type'])

        # Generate the menus for the display
        G.HabitMenu = M.Menu(habit_items, "Habits")
        G.DailyMenu = M.Menu(dailies_items, "Dailies")
        G.TODOMenu  = M.Menu(todos_items, "TODOs")


    # Write back changes to the server and update the interface
    def Flush(self,flush_for_quit=False):

        #TODO: most of this should not happen in the request manager
        import content as CT

        DEBUG.Display("Please Wait...")

        Drops = list()

        # Difference obtained in user stats due to these operations
        origDict = {'hp': G.user.hp, 'gp': G.user.gp, 'mp': G.user.mp,
                    'exp': G.user.exp, 'lvl': G.user.lvl}
        diffDict = origDict.copy()

        #
        #
        #
        # Habits marked as +
        for i in self.MarkUpQueue:
            logger.debug("Marking '%s' up" % str(i.taskname))
            json = self.ScoreTask(i.task.taskID,'up')

            for i in diffDict:
                diffDict[i] = json[i]

            # Check for drops
            tmpdrp = CT.CheckDrops( json['_tmp'] )
            if( tmpdrp is not None):
                Drops.append(tmpdrp)

        #
        #
        #
        # Habits marked as -
        for i in self.MarkDownQueue:
            logger.debug("Marking '%s' down" % str(i))
            json = self.ScoreTask(i.task.taskID,'down')

            for i in diffDict:
                diffDict[i] = json[i]

        #
        #
        #
        # Dailies and TODOS marked as completed
        for i in self.MarkQueue:
            direction = None
            if i.task.task_type != "daily" or (not i.task.completed):
                direction = "up"
            else:
                direction = "down"

            if (direction is None):
                continue

            json = self.ScoreTask(i.task.taskID,direction)

            if i.task.task_type == "todo":
                G.TODOMenu.Remove(i.task.taskID)
            elif i.task.task_type == "daily":
                i.task.completed ^= True

            for i in diffDict:
                diffDict[i] = json[i]

            # Check for drops
            tmpdrp = CT.CheckDrops( json['_tmp'] )
            if( tmpdrp is not None):
                Drops.append(tmpdrp)

        #
        #
        #
        for i in self.DeleteQueue:
            self.DeleteTask(i.task.taskID)

            if i.task.task_type == "habit":
                G.HabitMenu.Remove(i.task.taskID)
            elif i.task.task_type == "daily":
                G.DailyMenu.Remove(i.task.taskID)
            elif i.task.task_type == "todo":
                G.TODOMenu.Remove(i.task.taskID)

        #
        #
        #
        for i in self.EditQueue:
            self.UpdateTask(i.task.taskID, i.task.data)

        if(flush_for_quit):
            return

        #
        #
        # Update the Interface
        G.screen.Erase()
        G.user.PrintDiff(diffDict)
        G.intf.Init()
        G.user.PrintUserStats()

        #
        #
        #
        # Display Drop Messages
        if Drops:
            G.screen.SaveInRegister(1)
            drop_items = []
            for i in Drops:
                DEBUG.Display("Processing Drop %s..." % i);
                drop_items += [M.SimpleTextItem(i)]

            dropMenu = M.SimpleTextMenu(drop_items, C.SCR_TEXT_AREA_LENGTH)
            dropMenu.SetXY(C.SCR_FIRST_HALF_LENGTH, 5)
            dropMenu.Display()
            dropMenu.Input()
            G.screen.RestoreRegister(1)

        self.ClearQueues()


