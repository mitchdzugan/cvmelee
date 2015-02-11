import cv2

CV_CAP_PROP_POS_MSEC = 0
CV_CAP_PROP_POS_FRAMES = 1
CV_CAP_PROP_POS_AVI_RATIO = 2
CV_CAP_PROP_FRAME_WIDTH = 3
CV_CAP_PROP_FRAME_HEIGHT = 4
CV_CAP_PROP_FPS = 5
CV_CAP_PROP_FOURCC = 6
CV_CAP_PROP_FRAME_COUNT = 7
CV_CAP_PROP_FORMAT = 8
CV_CAP_PROP_MODE = 9
CV_CAP_PROP_BRIGHTNESS = 10
CV_CAP_PROP_CONTRAST = 11
CV_CAP_PROP_SATURATION = 12
CV_CAP_PROP_HUE = 13
CV_CAP_PROP_GAIN = 14
CV_CAP_PROP_EXPOSURE = 15
CV_CAP_PROP_CONVERT_RGB = 16
CV_CAP_PROP_WHITE_BALANCE = 17
CV_CAP_PROP_RECTIFICATION = 18

class MeleeCapture:
	def __init__(self, filename):
		self.capture = cv2.VideoCapture(filename)
		self.width = self.capture.get(CV_CAP_PROP_FRAME_WIDTH)
		self.height = self.capture.get(CV_CAP_PROP_FRAME_HEIGHT)
		self.totalFrames = self.capture.get(CV_CAP_PROP_FRAME_COUNT)
		self.fps = self.capture.get(CV_CAP_PROP_FPS)

	def readFrame(self, frameIndex):
		self.capture.set(CV_CAP_PROP_POS_FRAMES, frameIndex)
		frame = self.cap.read()[1]
		return frame
