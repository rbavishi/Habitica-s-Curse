""" Module "User" : User stats and profile

    All user related data such as health, gold, mana etc. are stored here
"""
# Standard Library Imports
import time
import datetime

# Custom Module Imports

import config as C
import global_objects as G
import debug as DEBUG
import request_manager as RM
import helper as H
import menu as M
import content as CT


def Round(num):
    if num < 0:
	return -1 * int(round(abs(num), 0))
    return int(round(num, 0))


# Display positive numbers as +N and negative numbers as -N 
def SignFormat(num):
    if num == 0:
        return ""

    return '{0:+d}'.format(num)


class User(object):
    """ Class to store user data """

    def __init__(self, data):
 
        self.data = data
	self.stats = data['stats']

        # Basic User Stats
        self.hp          = Round(self.stats['hp'])
        self.maxHealth   = Round(self.stats['maxHealth'])
        self.mp          = int(self.stats['mp'])
        self.maxMP       = Round(self.stats['maxMP'])
        self.gp          = int(self.stats['gp'])
        self.exp         = int(self.stats['exp'])
        self.toNextLevel = Round(self.stats['toNextLevel'])
        self.lvl         = self.stats['lvl']
	
	# Stats, gear etc.
	# Strength, Intelligence, Perception, Constitution
	self.attrStats   = {} # Will be updated when habitica content is fetched
	self.equipGear   = self.data['items']['gear']['equipped']

        self.cursorPositions = []

    # Written separately to avoid confusion
    def Reload(self, data):
        self.data = data
	self.stats = data['stats']

        # Basic User Stats
        self.hp          = Round(self.stats['hp'])
        self.maxHealth   = Round(self.stats['maxHealth'])
        self.mp          = int(self.stats['mp'])
        self.maxMP       = Round(self.stats['maxMP'])
        self.gp          = int(self.stats['gp'])
        self.exp         = int(self.stats['exp'])
        self.toNextLevel = Round(self.stats['toNextLevel'])
        self.lvl         = self.stats['lvl']

	# Stats, gear etc.
	# Strength, Intelligence, Perception, Constitution
	self.attrStats   = H.GetUserStats(data) 
	self.equipGear   = self.data['items']['gear']['equipped']

    def PrintData(self):
        G.screen.DisplayCustomColor(" "*(C.SCR_Y-1), C.SCR_COLOR_WHITE_GRAY_BGRD, C.SCR_X-2, 0)

        cursor = 1
        self.cursorPositions = []

        # Level
        string = C.SYMBOL_LEVEL + " " + str(self.lvl)
        G.screen.DisplayCustomColorBold(string, C.SCR_COLOR_WHITE_GRAY_BGRD, C.SCR_X-2, cursor)

        self.cursorPositions.append(cursor)
        cursor += len(string) + 3 - len(C.SYMBOL_LEVEL)

        # Health
        string = C.SYMBOL_HEART + " " + str(self.hp)+"/"+str(self.maxHealth)
        G.screen.DisplayCustomColorBold(string, C.SCR_COLOR_RED_GRAY_BGRD, C.SCR_X-2, cursor)

        self.cursorPositions.append(cursor)
        cursor += len(string) + 3 - len(C.SYMBOL_HEART)

        # XP
        string = C.SYMBOL_EXPERIENCE + " " + str(self.exp)+"/"+str(self.toNextLevel)
        G.screen.DisplayCustomColorBold(string, C.SCR_COLOR_GREEN_GRAY_BGRD, C.SCR_X-2, cursor)

        self.cursorPositions.append(cursor)
        cursor += len(string) + 3 - len(C.SYMBOL_EXPERIENCE)

        # Mana
        string = C.SYMBOL_MANA + " " + str(self.mp)+"/"+str(self.maxMP)
        G.screen.DisplayCustomColorBold(string, C.SCR_COLOR_BLUE_GRAY_BGRD, C.SCR_X-2, cursor)

        self.cursorPositions.append(cursor)
        cursor += len(string) + 3 - len(C.SYMBOL_MANA)

        # Gold
        string = C.SYMBOL_GOLD + " " + str(self.gp)
        G.screen.DisplayCustomColorBold(string, C.SCR_COLOR_YELLOW_GRAY_BGRD, C.SCR_X-2, cursor)

        self.cursorPositions.append(cursor)
        cursor += len(string) + 3 - len(C.SYMBOL_GOLD)

	# Last Update
	string = "Last Update: " + G.LastUpdate.strftime("%H:%M:%S %d/%m")
	G.screen.DisplayCustomColorBold(string, C.SCR_COLOR_MAGENTA_GRAY_BGRD, C.SCR_X-2, cursor)

        self.cursorPositions.append(cursor)
	cursor += len(string) + 1
	self.cursorPositions.append(cursor)


    def PrintUserStats(self, cursor=-1):
	if cursor == -1:
	    cursor = self.cursorPositions[-1]

	string = ("STR: " + str(self.attrStats['str']) + " " +
		  "INT: " + str(self.attrStats['int']) + " " +
		  "PER: " + str(self.attrStats['per']) + " " + 
		  "CON: " + str(self.attrStats['con']))

	G.screen.DisplayCustomColorBold(string, C.SCR_COLOR_MAGENTA_GRAY_BGRD, C.SCR_X-2, C.SCR_Y-(3 + len(string)))

    def PrintDiff(self, newDict):
	diffDict = {}

	diffDict['hp'] = Round(newDict['hp']) - self.hp; self.hp = Round(newDict['hp']); self.stats['hp'] = newDict['hp']
	diffDict['mp'] = int(newDict['mp']) - self.mp; self.mp = int(newDict['mp']); self.stats['mp'] = newDict['mp']
	diffDict['gp'] = int(newDict['gp']) - self.gp; self.gp = int(newDict['gp']); self.stats['gp'] = newDict['gp']
	diffDict['exp'] = int(newDict['exp']) - self.exp; self.exp = int(newDict['exp']); self.stats['exp'] = newDict['exp']
	diffDict['lvl'] = newDict['lvl'] - self.lvl; self.lvl = newDict['lvl']; self.stats['lvl'] = newDict['lvl']

	for i in diffDict:
	    diffDict[i] = SignFormat(diffDict[i])

        # Difficult to maintain the correct increase in experience when level changes
        if diffDict['lvl'] != "":
            diffDict['exp'] = ""

        # Level
        G.screen.DisplayCustomColorBold(diffDict['lvl'], C.SCR_COLOR_WHITE, C.SCR_X-1, self.cursorPositions[0]+2)
                     
        # Health
        G.screen.DisplayCustomColorBold(diffDict['hp'], C.SCR_COLOR_RED, C.SCR_X-1, self.cursorPositions[1]+2)

        # Experience
        G.screen.DisplayCustomColorBold(diffDict['exp'], C.SCR_COLOR_GREEN, C.SCR_X-1, self.cursorPositions[2]+2)
                     
        # Mana
        G.screen.DisplayCustomColorBold(diffDict['mp'], C.SCR_COLOR_BLUE, C.SCR_X-1, self.cursorPositions[3]+2)
                     
        # Gold
        G.screen.DisplayCustomColorBold(diffDict['gp'], C.SCR_COLOR_YELLOW, C.SCR_X-1, self.cursorPositions[4]+2)

    def GetPartyData(self):
        resp = G.reqManager.PartyRequest()

        # Need some error handling here
        if resp.status_code != 200:
            return 

        data = resp.json()
	partyObj = CT.Party(data)
	partyObj.Display()
