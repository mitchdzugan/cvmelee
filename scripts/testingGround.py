import os.path, sys
import cv2
from pprint import pprint
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from CVMelee.MeleeYoutubeProcessor import MeleeYoutubeProcessor
from CVMelee.PotentialROI import ROI
from CVMelee.parseVodsCo import run
from matplotlib import pyplot as plt

import httplib
import json

url = "stats-meleemetrics.herokuapp.com"
#url = "localhost:3000"

def createNew(u, j):
	headers = {"Content-type": "application/json",
	           "Accept": "application/json"}
	conn = httplib.HTTPConnection(url)
	conn.request("POST", u, j, headers)
	return int(json.loads(conn.getresponse().read())["id"])

def getAndCreateIfNew(u, j, k1, k2):
	conn = httplib.HTTPConnection(url)
	conn.request("GET", u + ".json")
	alreadyThere = json.loads(conn.getresponse().read())
	for thing in alreadyThere:
		if thing[k2] == json.loads(j)[k1][k2]:
			return int(thing["id"])
	return createNew(u, j)

def doesExist(j, k, v):
	for thing in j:
		if thing[k] == v:
			return True
	return False

ts = run()

for tournament in sorted(ts, key=lambda t: t.name):
	pprint(tournament.name)
	for group in tournament.sets:
		pprint(len(group.youtubeIds))
for tournament in sorted(ts, key=lambda t: t.name):
	#tournamentId = getAndCreateIfNew("/tournaments", tournament.toJson(), "tournament", "name")
	#conn = httplib.HTTPConnection(url)
	#conn.request("GET", "/youtube_vods.json")
	#j = json.loads(conn.getresponse().read())
	for group in tournament.sets:
		for vodId in group.youtubeIds:
			#if (doesExist(j, "urlid", vodId)):
			#	continue
			MYP = MeleeYoutubeProcessor(vodId)
			if MYP.run():
				pass
				#roiId = createNew("/rois", MYP.ROI.toJson(tournamentId))
				#vodId = createNew("/youtube_vods", MYP.toJson(roiId, "v1.0"))
				#for rg in MYP.rawgames:
				#	rgId = createNew("/raw_games", rg.toJson(vodId))
				#	for ps in rg.playerStates:
				#		rgpiId = createNew("/raw_game_port_infos", ps.toJson(rgId))
				#		for eJson in ps.eventsToJson(rgpiId):
				#			createNew("/events", eJson)
			#else:
			#	vodId = createNew("/youtube_vods", MYP.toJson(-1, "FAIL"))




# MYP = MeleeYoutubeProcessor("qiztB2plM7o").run()
"""
MYP.downloadVideo()
MYP.ROI = ROI()
MYP.ROI.setup(162,1118,0,710,0)

image = MYP.ROI.scopeImage(MYP.capture.readFrame(22708))

MYP.playerIconX += 0
MYP.playerIconY -= 0
for playerIcon in MYP.playerIcons:
	m = MYP.matchFromImage(MYP.playerIconX, MYP.playerIconX + 22, MYP.playerIconY, MYP.playerIconY + 20, image, playerIcon)
	pprint(m)
plt.imshow(image)
plt.show()
"""
"""
pprint(MYP.matchesFromFrame(cv2.imread("./media/sample1.png"), [1]))
pprint(MYP.matchesFromFrame(cv2.imread("./media/sample2.png"), [1]))
pprint(MYP.matchesFromFrame(cv2.imread("./media/sample3.png"), [1]))
pprint(MYP.matchesFromFrame(cv2.imread("./media/sample4.png"), [1]))
pprint(MYP.matchesFromFrame(cv2.imread("./media/sample5.png"), [1]))
pprint(MYP.matchesFromFrame(cv2.imread("./media/sample6.png"), [1]))
pprint(MYP.matchesFromFrame(cv2.imread("./media/sample8.png"), [1]))
pprint(MYP.matchesFromFrame(cv2.imread("./media/sample9.png"), [1]))
pprint(MYP.matchesFromFrame(cv2.imread("./media/sample10.png"), range(4)))
"""
"""
headers = {"Content-type": "application/json",
           "Accept": "application/json"}

body = json.dumps({
	"tournament": {
		"name": "MAYLAYYYY",
		"onday": "2004-02-12"
	}})
pprint(body)
conn = httplib.HTTPConnection("localhost:3000")
conn.request("POST", "/tournaments", body, headers)
response = conn.getresponse()
pprint(response.status)
pprint(response.reason)
pprint(response.read())
"""
