""" Module "Content" : Manage Habitica Content

    All info related to quests, items etc. i.e. the basic Habitica Content
    is stored here. All fetching takes constant time.
"""

# Standard Library Imports
import time
import math

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

class ContentManager(object):
    """ Class for managing Habitica content """

    def __init__(self):
        #DEBUG.Display("Content Fetching in progress...")
        self.contentDict = G.reqManager.FetchGameContent()

    def Quest(self, key):
        return self.contentDict['quests'].get(key, {})

    def Equipment(self, key):
        return self.contentDict['gear']['flat'][key]


class Party(object):
    """ Class for storing party info, displaying chat menus,
        quest details(if any) etc. """

    def __init__(self, party):
        self.party = party

        logger.debug("Party Object - \n %s" % str(party))

        # Some Basic Details
        self.name    = str(party['name'])

        #self.members = [str(i['profile']['name']) for i in party['members']]
        # V3 changes, members don't work no more :(
        self.members = ['(Member list not implemented)']

        self.chat    = party['chat']
        chat_items = []
        chatList = self.chat[:50]
        for i in chatList:
            timeElapsed = H.GetDifferenceTime(i['timestamp'])
            detailString = i.get('user', '') + " " + timeElapsed
            chat_items += [M.SimpleTextItem(str(i['text']), additional=str(detailString))]

        self.chatMenu = M.SimpleTextMenu(chat_items, C.SCR_TEXT_AREA_LENGTH)

        self.quest = party.get('quest', None)
        logger.debug("Current Quest: %s" % str(self.quest))
        if self.quest != None:
            while (G.content == None):
                DEBUG.Display("Fetching Content...")
                time.sleep(5)
            DEBUG.Display(" ")

            self.questDetails = G.content.Quest(str(self.quest['key']))
            self.questText    = str(self.questDetails['text'])

            self.questType = ""
            self.progress = 0

            if self.questDetails.has_key('boss'):
                self.questType     = "boss"
                self.bossMaxHealth = self.questDetails['boss']['hp']
                self.bossName      = self.questDetails['boss']['name']
                self.bossRage      = self.questDetails['boss'].get('rage', None)
                self.bossStrength  = self.questDetails['boss']['str']

                if(party['quest']['active']):
                    self.progress      = int(round(party['quest']['progress']['hp'],0))

            elif self.questDetails.has_key('collect'):
                self.questType     = "collect"
                self.questItems    = self.questDetails['collect']

                if(party['quest']['active']):
                    self.progress      = party['quest']['progress']['collect']


    def Display(self):
        G.screen.ClearTextArea()
        X, Y = C.SCR_FIRST_HALF_LENGTH-2, 1
        MAX_X = C.SCR_X - 3

        titleString = "".join([self.name, " : "]+[i+", " for i in self.members[:-1]]+[self.members[-1]])
        G.screen.Display(titleString, X, Y,color=C.SCR_COLOR_MAGENTA,bold=True)
        G.screen.Display("-"*(C.SCR_Y-2), X+1, Y,color=C.SCR_COLOR_LIGHT_GRAY)
        X += 2

        if self.quest != None and self.party['quest']['active'] == True:
            G.screen.Display("Quest: "+self.questText, X, Y,bold=True)
            X += 1
            if self.questType == "boss":
                # Display Boss Stats
                G.screen.Display(str(self.bossName)+" "+C.SYMBOL_HEART+" : "+
                                 str(self.progress)+"/"+str(self.bossMaxHealth),MAX_X, Y,
                                 color=C.SCR_COLOR_RED, bold=True)

                MAX_X -= 1

            elif self.questType == "collect":
                # Display Collect Statistics
                disp_string = "Collect "
                for (key, value) in self.questItems.items():
                    disp_string += value['text'] + " : " + str(self.progress[key]) + "/" + str(value['count']) + " "

                G.screen.Display(disp_string, MAX_X, Y,
                                 color=C.SCR_COLOR_YELLOW, bold=True)
                MAX_X -= 1


        self.chatMenu.SetXY(X+1, 1)
        self.chatMenu.SetNumRows(MAX_X - (X + 1))
        self.chatMenu.Display()
        self.chatMenu.Input()

def CheckDrops(response):
    drop = None
    if response.has_key('drop'):
        logger.debug("  Found a drop!\n%s" % str(response))
        if response['drop'].has_key('dialog'):
            drop=str(response['drop']['dialog'])
        elif response['drop'].has_key('text'):
            drops=str(response['drop']['text'])
        elif response['drop'].has_key('notes'):
            drop=str(response['drop']['notes'])

    return drop

def EffectiveValueTask(value): # Value used for calculation of damages.
                               # Between -47.27 and 21.27
    if value < -47.27:
        return -47.27
    if value > 21.27:
        return 21.27

    return value


def GetData():

    DEBUG.Display("Please Wait...")
    data = G.reqManager.FetchUserData()
    DEBUG.Display(" ")

    # Calculate Damage to User
    while (G.content == None):
        DEBUG.Display("Fetching Content...")
        time.sleep(5)
    DEBUG.Display(" ")

    userStats = H.GetUserStats(data)
    stealth = data['stats']['buffs']['stealth']
    conBonus = max(1 - (userStats['con']*(1.0/250)), 0.1)


    userDamage = 0
    partyDamage = 0
    userDamageBoss = 0

    party = data['party']
    quest = party.get('quest', {})
    if quest != {}:
        questDetails = G.content.Quest(quest['key'])
        userDamageBoss = math.floor(quest['progress']['up']*10)/10

    dailies = G.reqManager.FetchUserTasks("dailys")
    dailiesIncomplete = 0

    for daily in dailies:
        logger.debug("Processing Daily: %s" % str(daily['text']))
        if not H.isDueDaily(daily) or daily['completed']:
            continue

        dailiesIncomplete += 1
        if stealth > 0:
            stealth -= 1
            continue

        checklist = daily['checklist']
        done = len([i for i in checklist if i['completed']])
        total = len(checklist)
        checklistProportionDone = 0.0

        if total > 0:
            checklistProportionDone = (done*1.0)/total

        damage = 0.9747**(EffectiveValueTask(daily['value']))
        damage = damage*(1 - checklistProportionDone)

        # Due To Boss
        if quest != {}:
            bossDamage = damage
            if questDetails.has_key('boss'):
                if daily['priority'] < 1:
                    bossDamage *= daily['priority']

                partyDamage += bossDamage * questDetails['boss']['str']

        userDamage += damage * conBonus * daily['priority'] * 2



    userDamage += partyDamage

    userDamage = math.ceil(userDamage*10)/10
    partyDamage = math.ceil(partyDamage*10)/10
    data_items = ["Current Health: "+str(G.user.hp), "Dailies Incomplete: "+str(dailiesIncomplete), "Est. Damage to You: "+str(userDamage), "Est. Damage to Party: "+str(partyDamage),
                  "Est. Damage to Boss: "+str(userDamageBoss)]

    # Collection statistics if it is a collect quest
    if questDetails.has_key('collect'):
        disp_string = "You have found "
        for (key, value) in quest['progress']['collect'].items():
            disp_string += str(value) + " " + questDetails['collect'][key]['text'] + " "
        data_items += [disp_string]


    data_items = [M.SimpleTextItem(i) for i in data_items]

    G.screen.SaveInRegister(1)
    dataMenu = M.SimpleTextMenu(data_items, C.SCR_TEXT_AREA_LENGTH)
    dataMenu.SetXY(C.SCR_FIRST_HALF_LENGTH, 5)
    dataMenu.Display()
    dataMenu.Input()
    G.screen.RestoreRegister(1)
