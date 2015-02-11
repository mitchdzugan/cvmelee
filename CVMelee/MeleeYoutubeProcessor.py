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

#-----------#

class MeleeYoutubeProcessor:
	def __init__(self, youtubeId):
		self.youtubeId = youtubeId
		self.youtubeUrl = 'https://www.youtube.com/watch?v=' + self.youtubeId

	def run(self):
		self.downloadVideo()
		self.findBoundingRect():
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
		self.yt.url = self.youtubeUrl
        video = self.yt.videos[-2]
        filePath = os.path.join("./media/videos/", video.filename)
        video.filename = filePath
        if (not os.path.exists(filePath + "." + video.extension)):
            video.download()
        self.capture = MeleeCapture(filePath + "." + video.extension)

    def incrementAsIf60fps(self, framesToIncIf60fps):
    	self.frameIndex += framesToIncIf60fps * self.capture.fps / 60
