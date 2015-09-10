class EndOfVODException(Exception):
	def __init__(self, frameIndex):
		self.frameIndex = frameIndex
	def __str__(self):
		return "Frame index: " + `self.frameIndex` + " is out of range"