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

#-----------#

class MeleeYoutubeProcessor:
	def __init__(self, youtubeId):
		self.youtubeId = youtubeId
		self.youtubeUrl = 'https://www.youtube.com/watch?v=' + self.youtubeId
		self.youtube = YouTube()

	def run(self):
		self.downloadVideo()
		self.findBoundingRect()
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
		self.PotentialROI = potentialROIFactory(self.capture.width, self.capture.height)

	def incrementAsIf60fps(self, framesToIncIf60fps):
		self.frameIndex += framesToIncIf60fps * self.capture.fps / 60

	def findBoundingRect(self):
		xs = {}
		ys = {}

		width = self.capture.width + 6
		height = self.capture.width + 6
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

		for frameIndex in range(0, self.capture.totalFrames, self.capture.totalFrames / 40):
			image = self.capture.readFrameWithBorder(frameIndex, 3)
			for roi in potentialROIs:
				scopedIm = cv2.resize(image[roi.ylow:roi.yhigh, roi.xlow:roi.xhigh], (1176,884))
				matches = self.matchesFromFrame(scopedIm, range(4))




























if __name__ == "__main__":
	MeleeYoutubeProcessor("yKsaRJDCWt8").run()
