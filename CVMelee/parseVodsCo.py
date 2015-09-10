from bs4 import BeautifulSoup
import urllib2
from pprint import pprint
from datetime import datetime
from time import sleep
import os.path
import json

g = {}
g["lastCalled"] = datetime.now()
g["count"] = 0
g["seenStrings"] = []

def downloadUrl(url, useCache = True):
    pprint("Downloading: " + url)
    fname = "./cache/" + url.split("vods.")[1].replace("?", "...")
    if useCache and os.path.isfile(fname):
        f = open(fname, "r")
        text = f.read()
        f.close()
        return text
    else:
        rightNow = datetime.now()
        diff = rightNow - g["lastCalled"]
        g["lastCalled"] = rightNow
        if diff.microseconds < 3000000:
            sleep((3000000.0 - diff.microseconds) / 1000000.0)
        text = urllib2.urlopen(url).read()
        f = open(fname, "w")
        f.write(text)
        f.close()
        return text

class Tournament:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.date = None
        self.sets = []
        soup = BeautifulSoup(downloadUrl('https://vods.co/melee?&&stage=All&event=' + `id` + '&&type=1'))
        while(1):
            spans = soup.find_all('span')
            for s in spans:
                if str(s['class'][0]) == 'date-display-single':
                    self.date = s.get_text()
                if str(s['class'][0]) == 'field-content':
                    self.sets.append(Set(s))
            atags = soup.find_all('a')

            stillGoing = False
            for atag in atags:
                try:
                    if str(atag['title']) == "Go to next page":
                        stillGoing = True
                        soup = BeautifulSoup(downloadUrl('https://vods.co' + atag['href']))
                        break
                except:
                    pass
            if not stillGoing:
                break

    def toJson(self):
        return json.dumps({"tournament": {
            "name": str(self.name),
            "onday": str(self.date)
        }})

class Game:
    def __init__(self, lines):
        g["count"] += 1
        #pprint(g["count"])
        self.char1 = lines[1]
        self.char2 = lines[2].split(" vs ")[1]
        self.stage = lines[3].split(" - ")[1]

    def __str__(self):
        return str({
            "char1" : self.char1,
            "char2" : self.char2,
            "stage" : self.stage
        })

    def toJson(self, rawGameId, gameGroupId):
        return json.dumps({"game": {
            "stage": str(self.stage),
            "rawgame_id": rawGameId,
            "gamegroup_id": gameGroupId
            }})

class Set:
    def __init__(self, s):
        self.youtubeIds = []
        lines = s.get_text("\n").split("\n")
        if not (lines[-1].split("/")[0] in g["seenStrings"]):
            pprint(lines[-1].split("/")[0])
            g["seenStrings"].append(lines[-1].split("/")[0])
        if "Crew" in lines[1] or "PARTIAL" in lines[1] or "Ironman" in lines[1]:
            return
        self.gameLimit = None # int(lines[1].split("[Best of ")[1].split("]")[0])
        self.games = []
        i = 2
        while(1):
            if not "Game" in lines[i]:
                if "Game" in lines[i+1]:
                    i += 1
                else:
                    break
            self.games.append(Game(lines[i:i+4]))
            i += 5

        playersLine = next((line for line in lines[i:] if line.count("vs") > 0), None)
        if len([line for line in lines[i:] if line.count("vs") > 0]) > 1:
            print(lines[i:])
        if playersLine != None:
            self.player1 = playersLine.split(" vs ")[0]
            self.player2 = playersLine.split(" vs ")[1]
        else:
            print(lines[i:])

        self.youtubeIds = [
            seg.split("?")[0] for seg in downloadUrl("https://vods.co" + s.a['href']).split("www.youtube.com/embed/")[1:]]

    def __str__(self):
        return str({
            "gameLimit" : self.gameLimit,
            "games" : self.games,
            "player1" : self.player1,
            "player2" : self.player2,
            "youtubeIds" : self.youtubeIds
        })

    #def toJson(self, )

def run():
    soup = BeautifulSoup(downloadUrl('https://vods.co/melee', False))
    return [Tournament(
        int(option["value"]),
        str(option.get_text()))
     for option in soup.find(id='edit-event').find_all('option') if str(option["value"]) != "All"]

