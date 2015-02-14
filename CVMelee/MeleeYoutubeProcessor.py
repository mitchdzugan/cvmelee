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
from CVMelee.PotentialROI import potentialROIFactoryFactory
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
		self.potentialROIFactory = potentialROIFactoryFactory(self.capture.width, self.capture.height)

	def incrementAsIf60fps(self, framesToIncIf60fps):
		self.frameIndex += framesToIncIf60fps * self.capture.fps / 60

	def inResolutionRange(self, xlow, xhigh, ylow, yhigh):
		resolution = (float(xhigh - xlow)) / (yhigh - ylow)
		return (abs(resolution - 1.333) < 0.05 or abs(resolution - 1.62) < 0.05) and ((xhigh - xlow) * (yhigh - ylow) * 2 > self.capture.width * self.capture.height)

	def findMeleesROI(self):
		pprint("1")
		images = [self.capture.readFrame(i) for i in range(0, self.capture.totalFrames, self.capture.totalFrames / 40)]
		pprint("2")
		im = images[0]/40
		for imt in images[1:]:
			im = cv2.add(im, imt/40)

		gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
		edges = cv2.Canny(gray, 100, 100, apertureSize = 3)
		minLineLength = 100
		maxLineGap = 10
		lines = cv2.HoughLinesP(edges,1,np.pi/180,100,minLineLength,maxLineGap)
		if lines == None:
			lines = [[]]
		xlines = [0] + list(set([l[0] for l in lines[0] if l[0] == l[2]])) + [self.capture.width]
		pprint(xlines)
		ylines = [0] + list(set([l[1] for l in lines[0] if l[1] == l[3]])) + [self.capture.height]
		pprint(ylines)

		plt.imshow(im)
		plt.show()

		plt.imshow(edges)
		plt.show()


		xpairs = [[xlow, xhigh] for xlow in xlines for xhigh in xlines if (
			10 * (xhigh - xlow) > 6 * self.capture.width)]

		ypairs = [[ylow, yhigh] for ylow in ylines for yhigh in ylines if (
			10 * (yhigh - ylow) > 8 * self.capture.height)]

		ylowsAll  = sorted(list(set([y[0] for y in ypairs])), key=lambda y: -1*y)
		yhighsAll = sorted(list(set([y[1] for y in ypairs])), key=lambda y: 1*y)
		xlows  = sorted(list(set([x[0] for x in xpairs])), key=lambda x: -1*x)
		xhighs = sorted(list(set([x[1] for x in xpairs])), key=lambda x: 1*x)

		pprint(ylowsAll)
		pprint(yhighsAll)
		ylows = [ylowsAll.pop()]
		ylowCurr = ylows[0]
		while len(ylowsAll) > 0:
			y = ylowsAll.pop()
			if y - 3 > ylowCurr:
				ylows.append(y)
				ylowCurr = y

		yhighs = [yhighsAll.pop()]
		yhighCurr = yhighs[0]
		while len(yhighsAll) > 0:
			y = yhighsAll.pop()
			if y + 3 < yhighCurr:
				yhighs.append(y)
				yhighCurr = y
		
		potentialSubROIs = set([])
		potentialROIsChecked = set([])

		pprint(ylows)
		pprint(yhighs)
		pprint(xlows)
		pprint(xhighs)
		pprint("3")

		for borderThickness in range(0,24,3):
			#ylows.append(borderThickness)
			#yhighs = [y+3 for y in yhighs]
			#yhighs.append(self.capture.height + 2 * borderThickness)

			ylows = [0] + [y + borderThickness for y in ylows]
			yhighs = [y + borderThickness for y in yhighs] + [self.capture.height + 2 * borderThickness]

			self.PotentialROI = self.potentialROIFactory(borderThickness)
			allPotentialROIs = set([
			    self.PotentialROI(xlow, xhigh, 
			                      ylow, yhigh) for xlow in xlows
			                                   for xhigh in xhighs
			                                   for ylow in ylows
			                                   for yhigh in yhighs
			                                   if self.inResolutionRange(xlow, xhigh, ylow, yhigh)])

			potentialROIs = allPotentialROIs - potentialROIsChecked
			pprint([len(potentialROIs),len(allPotentialROIs),len(potentialROIsChecked)])

			maxFound = 0
			someFound = 0
			for frameIndex in range(0, self.capture.totalFrames, self.capture.totalFrames / 40):
				for ROI in potentialROIs:
					if frameIndex > 4 * self.capture.totalFrames / 40:
						ROI.subROIs = [subROI for subROI in ROI.subROIs if subROI.mmatchesFound > 0]
					if frameIndex > 9 * self.capture.totalFrames / 40:
						ROI.subROIs = [subROI for subROI in ROI.subROIs if subROI.mmatchesFound > 1]
						ROI.subROIs = [subROI for subROI in ROI.subROIs if subROI.matchesFound > 0]
				checkedROIs = set([ROI for ROI in potentialROIs if len(ROI.subROIs) == 0])
				potentialROIsChecked = potentialROIsChecked | checkedROIs
				potentialROIs = allPotentialROIs - potentialROIsChecked
				pprint(frameIndex)
				image = None
				for ROI in potentialROIs:
					if image == None:
						image = self.capture.readFrameWithBorder(frameIndex, borderThickness)
					foundPossibleMatch = False
					scopedIm = ROI.scopeImage(image)
					matches = self.matchesFromFrame(scopedIm, range(4))


					"""
					pprint(matches)
					drawScopedIm = scopedIm.copy()
					cv2.rectangle(drawScopedIm, (236,769), (302,817), (255,255,255))
					plt.imshow(drawScopedIm)
					plt.show()
					"""


					for match in matches:
						for m in match:
							if m["Match"] > 0.7:
								foundPossibleMatch = True
								break
					if foundPossibleMatch:
						pprint([ROI.xlow, ROI.xhigh, ROI.ylow, ROI.yhigh])
						for subROI in ROI.subROIs:
							scopedIm = cv2.resize(image[subROI.ylow:subROI.yhigh, subROI.xlow:subROI.xhigh], (1176,884))
							matches = self.matchesFromFrame(scopedIm, range(4))
							if any([m["Match"] > 0.8 for match in matches for m in match]):
								subROI.mmatchesFound += 1
								someFound = max(someFound, subROI.mmatchesFound)
							for match in matches:
								if match[0]["Match"] > 0.8 and match[1]["Match"] > 0.8:
									subROI.matchesFound += 1
									maxFound = max(maxFound, subROI.matchesFound)
									potentialSubROIs.add(subROI)
				#pprint(maxFound)
				#pprint(someFound)
				if maxFound > 3:
					break
			potentialROIsChecked = potentialROIsChecked | potentialROIs
			if maxFound > 3:
				break

		if not maxFound > 3:
			pprint("I DONT BELIEVE THIS IS A MELEE VIDEO")
			return

		foundCount = [0,0,0]
		for frameIndex in range(0, self.capture.totalFrames, self.capture.totalFrames / 40):
			pprint(frameIndex)
			longestMatches = [0,0,0,0]
			for subROI in potentialSubROIs:
				scopedIm = cv2.resize(
				    self.capture.readFrameWithBorder(
				    	frameIndex, subROI.borderThickness)[subROI.ylow:subROI.yhigh, subROI.xlow:subROI.xhigh], (1176,884))
				subROI.matches = self.matchesFromFrame(scopedIm, range(4))
				for i, match in enumerate(subROI.matches):
					for j, matchDigit in enumerate(match):
						if matchDigit["Match"] > 0.8:
							longestMatches[i] = max(j+1, longestMatches[i])

			for subROI in potentialSubROIs:
				for i, length in enumerate(longestMatches):
					for j in range(length):
						subROI.matchSum[j] += subROI.matches[i][j]["Match"]
			for length in longestMatches:
				for j in range(length):
					foundCount[j] += 1

			digitPlacesFound = 0
			totalCount = 0
			for count in foundCount:
				totalCount += count
				if count > 0:
					digitPlacesFound += 1
			if digitPlacesFound > 0:
				maxval = max(
				    potentialSubROIs, key=lambda subROI: subROI.matchSumAvg(foundCount)
				    ).matchSumAvg(foundCount) / digitPlacesFound

			if totalCount > 60:
				potentialSubROIs = [
				    subROI for subROI in potentialSubROIs if subROI.matchSumAvg(foundCount) / digitPlacesFound > 0.99 * maxval]
			elif totalCount > 50:
				potentialSubROIs = [
				    subROI for subROI in potentialSubROIs if subROI.matchSumAvg(foundCount) / digitPlacesFound > 0.95 * maxval]
			elif totalCount > 49:
				potentialSubROIs = [
				    subROI for subROI in potentialSubROIs if subROI.matchSumAvg(foundCount) / digitPlacesFound > 0.90 * maxval]
			elif totalCount > 44:
				potentialSubROIs = [
				    subROI for subROI in potentialSubROIs if subROI.matchSumAvg(foundCount) / digitPlacesFound > 0.75 * maxval]

			if all([count > 1000 for count in foundCount]):
				break

			if digitPlacesFound > 2:
				pprint(foundCount)
				pprint([[subROI.matchSum[0] / foundCount[0], subROI.matchSum[1] / foundCount[1], subROI.matchSum[2] / foundCount[2]] for subROI in potentialSubROIs])

		subROI = max(potentialSubROIs, key=lambda subROI: subROI.matchSumAvg(foundCount))
		pprint(subROI.xlow)
		pprint(subROI.xhigh)
		pprint(subROI.ylow)
		pprint(subROI.yhigh)
		
		"""
		for frameIndex in range(0, self.capture.totalFrames, self.capture.totalFrames / 40):
			image = self.capture.readFrameWithBorder(frameIndex, subROI.borderThickness)
			scopedIm = subROI.scopeImage(image)
			plt.imshow(scopedIm)
			plt.show()
		"""
		

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
