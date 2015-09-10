from pytube import YouTube
from pprint import pprint
import os
import os.path
import numpy as np
import cv2
from IPython import embed
from matplotlib import pyplot as plt
import operator
import random
from sets import Set
import json

#-----------#

from CVMelee.MeleeCapture import MeleeCapture
from CVMelee.PotentialROI import potentialROIFactoryFactory
from CVMelee.TemplateWithTransparency import numberTemplate, buttonsTemplate, playerIconTemplate
from CVMelee.PlayerState import PlayerState
from CVMelee.EndOfVODException import EndOfVODException

#-----------#

class Dummy:
	def __init__(self):
		self.fps = 0

class RawGame:
	def __init__(self,timeStamp, playerStates):
		self.timeStamp = timeStamp
		self.playerStates = playerStates

	def toJson(self, youtubeVodId):
		return json.dumps({"raw_game": {
			"youtube_vod_id": youtubeVodId,
			"timestamp": self.timeStamp
			}})

class MeleeYoutubeProcessor:
	def __init__(self, youtubeId):
		self.youtubeId = youtubeId
		self.youtubeUrl = 'https://www.youtube.com/watch?v=' + self.youtubeId
		self.youtube = YouTube()
		self.numbers = [
			numberTemplate(
				"./media/numbers/" + filename
				) for filename in os.listdir("./media/numbers/") if filename.endswith(".png")]
		self.percentLocations = {
		    "y" : 407,
		    "xs" : [128, 280, 432, 584]
		}
		self.playerIconX = 428
		self.playerIconY = 46
		self.buttonsX = 461
		self.buttonsY = 397
		self.playerIcons = [
			playerIconTemplate(
				"./media/pause/playerIcons/" + filename
				) for filename in os.listdir("./media/pause/playerIcons/") if filename.endswith(".png")]
		self.buttons = buttonsTemplate("./media/pause/buttons.png")

	def run(self):
		self.rawgames = []
		if not self.downloadVideo():
			return False
		if not self.findMeleesROI():
			pprint("Not a Melee VOD")
			return False
		self.frameIndex = 0
		while(self.processGame()):
			pprint([ps.percentList for ps in self.playerStates])
		return True

	def processGame(self):
		try:
			frameStart = self.frameIndex
			self.determinePorts()
			self.rollbackToGameStart(frameStart)
			frameStart = self.frameIndex
			self.getPlayByPlay()
			self.determineWinner()
			self.rawgames.append(RawGame(frameStart, self.playerStates))
			return True
		except EndOfVODException:
			return False


	def determinePorts(self):
		matchesFound = [0,0,0,0]
		while(1):
			image = self.ROI.scopeImage(self.capture.readFrame(self.frameIndex))
			matches = self.matchesFromFrame(image, range(4))
			self.ports = []
			for i in range(len(matches)):
				if matches[i][0]["Match"] > 0.8:
					matchesFound[i] += 1
					if matchesFound[i] > 1:
						self.ports.append(i)
			if len(self.ports) == 2:
				break
			self.incrementAsIf60fps(15)
		pprint(self.ports)

	def rollbackToGameStart(self, frameStart):
		self.frameIndex = frameStart
		while any([m[0]["Match"]<0.8 for m in self.matchesFromFrame(self.ROI.scopeImage(self.capture.readFrame(self.frameIndex)), self.ports)]):
			self.incrementAsIf60fps(5)

	def getPlayByPlay(self):
		playerStates = [PlayerState(self.frameIndex, self.ports[0] + 1),
		                PlayerState(self.frameIndex, self.ports[1] + 1)]
		while(1):
			image = self.ROI.scopeImage(self.capture.readFrame(self.frameIndex))
			playerStates[0].currentMatch, playerStates[1].currentMatch = self.matchesFromFrame(image, self.ports)
			for state in playerStates:
				percent = state.matchToPercent(state.currentMatch, 0.75)
				state.processPercent(percent, self.frameIndex)
			pprint([self.frameIndex, [playerStates[0].framesOfConsecNones, playerStates[0].stocks, playerStates[0].percent], 
			               [playerStates[1].framesOfConsecNones, playerStates[1].stocks, playerStates[1].percent]])
			self.incrementAsIf60fps(5)
			if all([state.framesOfConsecNones > 60 for state in playerStates]):
				break
		self.playerStates = playerStates

	def determineWinner(self):
		winner = None
		state0, state1 = self.playerStates
		if state0.stocks == 1 and state1.stocks > 1:
			pprint("By only 1 player had 1 stock")
			winner = state1.port
		elif state1.stocks == 1 and state0.stocks > 1:
			pprint("By only 1 player had 1 stock")
			winner = state0.port
		elif (abs(state0.framesOfConsecNones - state1.framesOfConsecNones) <= 20):
			winner = -1
			numFrames = min(state0.framesOfConsecNones, state1.framesOfConsecNones)
			foundPause = False
			for i in range(self.frameIndex-numFrames, self.frameIndex):
				image = self.ROI.scopeImage(self.capture.readFrame(i))
				if self.matchFromImage(self.buttonsX, self.buttonsX + 134,
				                       self.buttonsY, self.buttonsY + 36,
				                       image, self.buttons)  > 0.90:
					foundPause = True
					maxval = 0.0
					pausedPort = 1
					for i, j in [[i,j] for i in range(-5,5) for j in range(-5,5)]:
						for playerIcon in self.playerIcons:
							m = self.matchFromImage(self.playerIconX - i,
							                        self.playerIconX + 22 - i,
							                        self.playerIconY - j,
							                        self.playerIconY + 20 - j,
							                        image, playerIcon)
							if m > maxval:
								maxval = m
								pausedPort = int(playerIcon.name)
						if maxval > 0.9:
							break
					pprint(i)
					pprint(self.ROI.xlow)
					pprint(self.ROI.xhigh)
					pprint(self.ROI.ylow)
					pprint(self.ROI.yhigh)
					pprint(self.ROI.borderTop)
					pprint(self.ROI.borderBottom)
					pprint("By Pause")
					pprint(pausedPort)
					if pausedPort == state0.port:
						winner = state1.port
					else:
						winner = state0.port
					break
			if not foundPause:
				winner = min(self.playerStates, key=lambda s: s.percentList[-1][2]).port
				pprint("By Last hit")
		else:
			if state0.framesOfConsecNones > state1.framesOfConsecNones + 20 and state0.stocks == 1:
				pprint("By saw last stock lost")
				winner = state1.port
			elif state1.stocks == 1:
				pprint("By saw last stock lost")
				winner = state0.port

		state0.winner = winner == state0.port
		state1.winner = winner == state1.port
		pprint("WINNER'S PORT IS: " + `winner`)

	def endOfVideo(self):
		return self.frameIndex >= self.capture.totalFrames

	def downloadVideo(self):
		try:
			self.youtube.url = self.youtubeUrl
			video = self.youtube.filter('mp4')[-1]
			filePath = os.path.join("./cache/videos/", video.filename)
			video.filename = filePath
			pprint(video.filename)
			if (not os.path.exists(filePath + "." + video.extension)):
				video.download()
			return False
			self.capture = MeleeCapture(filePath + "." + video.extension)
			if self.capture.valid: 
				self.potentialROIFactory = potentialROIFactoryFactory(self.capture.width, self.capture.height)
				return False
			return False
		except:
			pprint("AYY")
			self.capture = Dummy()
			return False

	def incrementAsIf60fps(self, framesToIncIf60fps):
		self.frameIndex += framesToIncIf60fps * self.capture.fps / 60

	def inResolutionRange(self, xlow, xhigh, ylow, yhigh):
		resolution = (float(xhigh - xlow)) / (yhigh - ylow)
		return ((abs(resolution - 1.333) < 0.05 or abs(resolution - 1.62) < 0.05) and 
		       ((xhigh - xlow) * (yhigh - ylow) * 2 > self.capture.width * self.capture.height))

	def removeNeighbors(self, l):
		currExtreme = l.pop()
		newl = [currExtreme]
		while len(l) > 0:
			curr = l.pop()
			if abs(curr - currExtreme) > 3:
				currExtreme = curr
				newl.append(currExtreme)
		return newl

	def ROIsFromVideo(self, meleeImages):
		average = meleeImages[0].image/len(meleeImages)
		for meleeImage in meleeImages[1:]:
			average = cv2.add(average, meleeImage.image/len(meleeImages))
		gray = cv2.cvtColor(average, cv2.COLOR_BGR2GRAY)
		edges = cv2.Canny(gray, 100, 300, apertureSize = 3)
		minLineLength = 0
		maxLineGap = 0
		lines = cv2.HoughLinesP(edges,1,np.pi/180,100,minLineLength,maxLineGap)
		if lines == None:
			lines = [[]]
		pprint(lines)
		xlines = list(set([0] + [l[0] for l in lines[0] if l[0] == l[2] and abs(l[1] - l[3]) > self.capture.width/10] + [self.capture.width]))
		ylines = list(set([0] + [l[1] for l in lines[0] if l[1] == l[3] and abs(l[2] - l[0]) > self.capture.height/10] + [self.capture.height]))

		xlows = sorted(
			filter(lambda x: x < self.capture.width / 2, xlines), key=lambda x: -1*x)
		xhighs = sorted(
			filter(lambda x: not (x < self.capture.width / 2), xlines))
		ylows = self.removeNeighbors(sorted(
			filter(lambda y: y < self.capture.height / 2, ylines), key=lambda y: -1*y))
		yhighs = self.removeNeighbors(sorted(
			filter(lambda y: not (y < self.capture.height / 2), ylines)))

		pprint([[l[1], l[2] - l[0]] for l in lines[0] if l[1] == l[3]])
		pprint(xlows)
		pprint(xhighs)
		pprint(ylows)
		pprint(yhighs)

		possibleROILists = []
		for borderThickness in range(0,24,3):
			ROIFactory = self.potentialROIFactory(borderThickness)
			ylows = [0] + [y + borderThickness for y in ylows]
			yhighs = [y + borderThickness for y in yhighs] + [self.capture.height + 2 * borderThickness]
			possibleROILists.append(set([
			    ROIFactory(xlow, xhigh, 
			               ylow, yhigh) for xlow in xlows
			                            for xhigh in xhighs
			                            for ylow in ylows
			                            for yhigh in yhighs
			                            if self.inResolutionRange(xlow, xhigh, 
			                                                      ylow, yhigh)]))
			pprint(len(possibleROILists[-1]))
		return possibleROILists

	def ROIsForTournament(self):
		return Set()

	def findMeleesROI(self):
		meleeImages = [self.capture.readFrame(i) for i in range(0, self.capture.totalFrames, self.capture.totalFrames / 40)]
		possibleROILists = self.ROIsFromVideo(meleeImages)
		possibleROIsChecked = set([])
		for possibleROIList in possibleROILists:
			possibleROIListToCheck = possibleROIList - possibleROIsChecked
			numComparedPerDigit = [0,0,0]
			for imagesChecked, meleeImage in enumerate(meleeImages):
				pprint(imagesChecked)
				numFoundPerPort = [[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
				for ROI in possibleROIListToCheck:
					scopedIm = ROI.scopeImage(meleeImage)
					ROI.matches = self.matchesFromFrame(scopedIm, range(4))
					if any([m["Match"] > 0.7 for match in ROI.matches for m in match]):
						for subROI in ROI.subROIs:
							scopedIm = subROI.scopeImage(meleeImage)
							subROI.matches = self.matchesFromFrame(scopedIm, range(4))
							for i, matchDigit in enumerate(subROI.matches):
								for j, match in enumerate(matchDigit):
									if match["Match"] > 0.8:
										numFoundPerPort[i][j] += 1
				isNumPerPort = [
					[numFound > 5 or (numFound * 10 > 
						              len(possibleROIListToCheck)) for numFound in numFoundPerDigit]
					for numFoundPerDigit in numFoundPerPort]
				for i, isNumPerDigit in enumerate(isNumPerPort):
					for j, isNum in enumerate(isNumPerDigit):
						if isNum:
							numComparedPerDigit[j] += 1

							checkedROIs = set([
								ROI for ROI in possibleROIListToCheck if all(
									[m["Match"] <= 0.7 for match in ROI.matches for m in match])])
							possibleROIListToCheck = possibleROIListToCheck - checkedROIs
							possibleROIsChecked = possibleROIsChecked | checkedROIs
							for ROI in possibleROIListToCheck:
								for subROI in ROI.subROIs:
									subROI.matchSum[j] += subROI.matches[i][j]["Match"]
						else:
							break
				totalCount = sum(numComparedPerDigit)
				digitsCompared = [numCompared > 0 for numCompared in numComparedPerDigit].count(True)
				if imagesChecked > 4 and totalCount < 1: break
				if imagesChecked > 9 and totalCount < 8: break
				if imagesChecked > 14 and totalCount < 15: break
				if imagesChecked > 24 and totalCount < 22: break
				if imagesChecked > 29 and totalCount < 29: break
				if imagesChecked > 34 and totalCount < 36: break
				maxVal, maxROI = 0.0, None
				for ROI in possibleROIListToCheck:
					for subROI in ROI.subROIs:
						#pprint(subROI.matchSum)
						curVal = subROI.matchSumAvg(numComparedPerDigit)
						if curVal > maxVal:
							maxVal = curVal
							maxROI = subROI
				for ROI in possibleROIListToCheck:
					condition = lambda ignore: True
					if digitsCompared > 0: condition = lambda matchSumAvg: matchSumAvg > maxVal * 0.85
					if digitsCompared > 1: condition = lambda matchSumAvg: matchSumAvg > maxVal * 0.95
					if digitsCompared > 2: condition = lambda matchSumAvg: matchSumAvg > maxVal * 0.99
					ROI.subROIs = [subROI for subROI in ROI.subROIs if condition(subROI.matchSumAvg(numComparedPerDigit))]
				checkedROIs = set([ROI for ROI in possibleROIListToCheck if len(ROI.subROIs) == 0])
				possibleROIListToCheck = possibleROIListToCheck - checkedROIs
				possibleROIsChecked = possibleROIsChecked | checkedROIs
			if totalCount < 43:
				possibleROIsChecked = possibleROIsChecked | possibleROIListToCheck 
			else:
				pprint(maxVal)
				self.ROI = maxROI
				return True
		return False

	def matchFromImage(self, xLow, xHigh, yLow, yHigh, frame, template):
		window = frame[yLow:yHigh, xLow:xHigh]
		winFG = cv2.bitwise_and(window, window,
		                        mask = template.maskInv)
		mWindow = cv2.add(template.background, winFG)
		res = cv2.matchTemplate(mWindow, template.image,
		                        cv2.TM_CCOEFF_NORMED)
		_,matchVal,_,_ = cv2.minMaxLoc(res)
		return matchVal

	def matchesFromFrame(self, frame, cornerIndexes):
		matches = []
		percents = []
		yLow = self.percentLocations["y"]
		yHigh = self.percentLocations["y"] + 39
		for cornerX in [self.percentLocations["xs"][ind] for ind in cornerIndexes]:
			accdWidth = 0
			matchesPerPort = []
			for i in range(3):
				results = []
				for number in self.numbers:
					if (i == 0 and number.image.shape[1] != 37):
						xHigh = cornerX - 5 - accdWidth
					else:
						xHigh = cornerX - accdWidth
					xLow = xHigh - number.image.shape[1]
					m = self.matchFromImage(xLow, xHigh,
					                        yLow, yHigh, frame, number)
					results.append({"Match": m, "Name": number.name,
					                "Width": number.image.shape[1]})
				bestMatch = max(results, key=lambda r: r["Match"])
				matchesPerPort.append({
					"Match" : bestMatch["Match"],
					"Digit" : int(bestMatch["Name"])
				})
				if (i == 0 and bestMatch["Width"] != 37):
					accdWidth += bestMatch["Width"] + 1
				else:
					accdWidth += bestMatch["Width"] - 3
			matches.append(matchesPerPort)
		return matches

	def toJson(self, roiId, processedVersion):
		return json.dumps({"youtube_vod": {
			"urlid": self.youtubeId,
			"roi_id": roiId,
			"fps": self.capture.fps,
			"processedversion": processedVersion
			}})




























if __name__ == "__main__":
	MeleeYoutubeProcessor("yKsaRJDCWt8").run()
