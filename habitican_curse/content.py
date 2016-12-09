""" Module "Content" : Manage Habitica Content

    All info related to quests, items etc. i.e. the basic Habitica Content
    is stored here. All fetching takes constant time.
"""

# Standard Library Imports
import requests
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
import request_manager as RM

FETCH_URL = "https://habitica.com:443/api/v2/content"

class ContentManager(object):
    """ Class for managing Habitica content """

    def __init__(self):
	#DEBUG.Display("Content Fetching in progress...")
	resp = self.Fetch()
	if resp.status_code == 200:
	    self.contentDict = resp.json()

	else:
	    self.contentDict = -1

    def Fetch(self):
	resp = requests.get(FETCH_URL)
	return resp

    def Quest(self, key):
	return self.contentDict['quests'].get(key, {})

    def Equipment(self, key):
	return self.contentDict['gear']['flat'][key]


class Party(object):
    """ Class for storing party info, displaying chat menus, 
    	quest details(if any) etc. """

    def __init__(self, party):
	self.party = party

	# Some Basic Details
	self.name    = str(party['name'])
	self.members = [str(i['profile']['name']) for i in party['members']]
	self.chat    = party['chat']
	chat_items = []
	chatList = self.chat[:50]
	for i in chatList:
	    timeElapsed = H.GetDifferenceTime(i['timestamp'])
	    detailString = i.get('user', '') + " " + timeElapsed
	    chat_items += [M.SimpleTextItem(str(i['text']), additional=str(detailString))]

	self.chatMenu = M.SimpleTextMenu(chat_items, C.SCR_TEXT_AREA_LENGTH)

	self.quest = party.get('quest', None)
	if self.quest != None:
	    while (G.content == None):
		DEBUG.Display("Fetching Content...")
		time.sleep(5)
	    DEBUG.Display(" ")

	    self.questDetails = G.content.Quest(str(self.quest['key']))
	    self.questText    = str(self.questDetails['text'])

	    self.questType = ""

	    if self.questDetails.has_key('boss'):
		self.questType     = "boss"
		self.bossMaxHealth = self.questDetails['boss']['hp']
		self.bossName      = self.questDetails['boss']['name']
		self.bossRage      = self.questDetails['boss'].get('rage', None)
		self.bossStrength  = self.questDetails['boss']['str']

		self.progress      = int(round(party['quest']['progress']['hp'],0))

	    elif self.questDetails.has_key('collect'):
		self.questType     = "collect"
		self.questItems    = self.questDetails['collect']
		self.progress      = party['quest']['progress']['collect']


    def Display(self):
	G.screen.ClearTextArea()
	X, Y = C.SCR_FIRST_HALF_LENGTH-2, 1
	MAX_X = C.SCR_X - 3

	titleString = "".join([self.name, " : "]+[i+", " for i in self.members[:-1]]+[self.members[-1]])
	G.screen.DisplayCustomColorBold(titleString, C.SCR_COLOR_MAGENTA, X, Y)
	G.screen.DisplayCustomColor("-"*(C.SCR_Y-2), C.SCR_COLOR_LIGHT_GRAY, X+1, Y)
	X += 2

	if self.quest != None and self.party['quest']['active'] == True:
	    G.screen.DisplayBold("Quest: "+self.questText, X, Y)
	    X += 1
	    if self.questType == "boss":
		# Display Boss Stats
		G.screen.DisplayCustomColorBold(str(self.bossName)+" "+C.SYMBOL_HEART+" : "+
					 str(self.progress)+"/"+str(self.bossMaxHealth), 
					 C.SCR_COLOR_RED, MAX_X, Y)

		MAX_X -= 1

  	    elif self.questType == "collect":
	        # Display Collect Statistics
		disp_string = "Collect "
		for (key, value) in self.questItems.items():
		    disp_string += value['text'] + " : " + str(self.progress[key]) + "/" + str(value['count']) + " "

		G.screen.DisplayCustomColorBold(disp_string, C.SCR_COLOR_YELLOW, MAX_X, Y)
		MAX_X -= 1


	self.chatMenu.SetXY(X+1, 1) 
	self.chatMenu.SetNumRows(MAX_X - (X + 1))
	self.chatMenu.Display()
	self.chatMenu.Input()

def EffectiveValueTask(value): # Value used for calculation of damages.
    			       # Between -47.27 and 21.27
    if value < -47.27:
	return -47.27
    if value > 21.27:
	return 21.27

    return value


def GetData():
    DEBUG.Display("Please Wait...")
    resp = requests.get(RM.GET_USER_URL, headers=G.reqManager.headers)
    DEBUG.Display(" ")

    # Need some error handling here
    if resp.status_code!=200:
	return

    data = resp.json()

    # Calculate Damage to User
    while (G.content == None):
	DEBUG.Display("Fetching Content...")
	time.sleep(5)
    DEBUG.Display(" ")

    userStats = H.GetUserStats(data)
    stealth = data['stats']['buffs']['stealth']
    dailies = data['dailys']
    conBonus = max(1 - (userStats['con']*(1.0/250)), 0.1)
    dailies = ([dailies]) if type(dailies) != list else dailies
    userDamage = 0
    partyDamage = 0
    userDamageBoss = 0

    party = data['party']
    quest = party.get('quest', {})
    if quest != {}:
	questDetails = G.content.Quest(quest['key'])
	userDamageBoss = math.floor(quest['progress']['up']*10)/10

    dailiesIncomplete = 0

    for daily in dailies:
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
