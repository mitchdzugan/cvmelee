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

#-----------#

from CVMelee.MeleeCapture import MeleeCapture
from CVMelee.PotentialROI import potentialROIFactory
from CVMelee.TemplateWithTransparency import numberTemplate

#-----------#

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
            "y" : 768,
            "xs" : [235, 514, 793, 1071]
        }

	def run(self):
		self.downloadVideo()
		self.findMeleesROI()
		self.frameIndex = 0
		while(not self.endOfVideo()):
			self.processGame()

	def processGame(self):
		self.determinePorts()
		self.rollbackToGameStart()
		self.getPlayByPlay()
		self.determineWinner()

	def endOfVideo(self):
		return self.frameIndex < self.capture.totalFrames

	def downloadVideo(self):
		self.youtube.url = self.youtubeUrl
		video = self.youtube.videos[-2]
		filePath = os.path.join("./media/videos/", video.filename)
		video.filename = filePath
		if (not os.path.exists(filePath + "." + video.extension)):
			video.download()
		self.capture = MeleeCapture(filePath + "." + video.extension)
		self.PotentialROI = potentialROIFactory(self.capture.width + 6, self.capture.height + 6)

	def incrementAsIf60fps(self, framesToIncIf60fps):
		self.frameIndex += framesToIncIf60fps * self.capture.fps / 60

	def findMeleesROI(self):
		xs = {}
		ys = {}

		width = self.capture.width + 6
		height = self.capture.height + 6
		for frameIndex in range(0, self.capture.totalFrames, self.capture.totalFrames / 40):
			pprint(frameIndex)

			image = self.capture.readFrameWithBorder(frameIndex, 3)
			gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			edges = cv2.Canny(gray, 100, 300, apertureSize = 3)
			minLineLength = 100
			maxLineGap = 100
			lines = cv2.HoughLinesP(edges,1,np.pi/180,100,minLineLength,maxLineGap)
			if lines == None:
				lines = [[]]
			xlines = [0] + list(set([l[0] for l in lines[0] if l[0] == l[2]])) + [width]
			ylines = [0] + [height]
			for x in xlines:
				if not (x in xs):
					xs[x] = set([])
				xs[x].add(frameIndex)
			for y in ylines:
				if not (y in ys):
					ys[y] = set([])
				ys[y].add(frameIndex)

		xlines = sorted(xs.items(), key=lambda x: x[0])
		ylines = sorted(ys.items(), key=lambda y: y[0])

		potentialROIs = [
			self.PotentialROI(xlines[i][0],  xlines[j][0],
			                  ylines[k][0],  ylines[l][0],
			                  xlines[i][1] & xlines[j][1] &
			                  ylines[k][1] & ylines[l][1]) for i in range(len(xlines))
			                                               for j in range(i+1, len(xlines))
			                                               for k in range(len(ylines))
			                                               for l in range(k+1, len(ylines))]

		potentialROIs = [p for p in potentialROIs if 2 * (p.xhigh-p.xlow) * (p.yhigh-p.ylow) > self.capture.height * self.capture.width]
		potentialROIs = [p for p in potentialROIs if len(p.frameSet) > 0]
		potentialROIs = sorted(potentialROIs, key=lambda p: len(p.frameSet))
		pprint(len(potentialROIs))

		eliminatedBulk = False
		potentialSubROIs = set([])
		for frameIndex in range(0, self.capture.totalFrames, self.capture.totalFrames / 40):
			pprint(frameIndex)
			pprint(eliminatedBulk)
			image = self.capture.readFrameWithBorder(frameIndex, 3)
			longestMatches = [0,0,0,0]
			for ROI in potentialROIs:
				ROI.foundMatch = False
				ROI.foundPossibleMatch = False
				scopedIm = cv2.resize(image[ROI.ylow:ROI.yhigh, ROI.xlow:ROI.xhigh], (1176,884))
				matches = self.matchesFromFrame(scopedIm, range(4))
				for match in matches:
					for m in match:
						if m["Match"] > 0.7:
							ROI.foundPossibleMatch = True
							break
				if ROI.foundPossibleMatch or eliminatedBulk:
					for subROI in ROI.subROIs:
						scopedIm = cv2.resize(image[subROI.ylow:subROI.yhigh, subROI.xlow:subROI.xhigh], (1176,884))
						subROI.matches = self.matchesFromFrame(scopedIm, range(4))
						for i, match in enumerate(subROI.matches):
							for j, digitMatch in enumerate(match):
								if digitMatch["Match"] > 0.8:
									ROI.foundMatch = True
								else:
									longestMatches[i] = max(j, longestMatches[i])
									break
			pprint(longestMatches)
			if any([length > 0 for length in longestMatches]):
				for ROI in potentialROIs:
					if ROI.foundMatch:
						ROI.matchesFound += 1
					if eliminatedBulk:
						for subROI in ROI.subROIs:
							for i, length in enumerate(longestMatches):
								for j in range(length):
									subROI.matchSum += subROI.matches[i][j]["Match"]
			if any([ROI.matchesFound > 1 for ROI in potentialROIs]):
				eliminatedBulk = True
				potentialROIs = [ROI for ROI in potentialROIs if ROI.matchesFound > 0]
		pprint(potentialROIs)


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
		yLow = self.percentLocations["y"] - 19
		yHigh = self.percentLocations["y"] - 19 + 69
		for cornerX in [self.percentLocations["xs"][ind] for ind in cornerIndexes]:
			accdWidth = 0
			matchesPerPort = []
			for i in range(3):
				results = []
				for number in self.numbers:
					if (i == 0 and number.image.shape[1] != 66):
						xHigh = cornerX - 10 - accdWidth
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
				if (i == 0 and bestMatch["Width"] != 66):
					accdWidth += bestMatch["Width"] + 7
				else:
					accdWidth += bestMatch["Width"] - 3
			matches.append(matchesPerPort)
		return matches




























if __name__ == "__main__":
	MeleeYoutubeProcessor("yKsaRJDCWt8").run()
