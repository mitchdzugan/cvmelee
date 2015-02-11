import cv2

class TemplateWithTransparency:
	def __init__(self, filePath, name):
		self.name = name
		self.image = cv2.imread(filePath)
		greyIm = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
		self.mask = cv2.inRange(greyIm, 179, 179)
		self.maskInv = cv2.bitwise_not(self.mask)
		self.background = cv2.bitwise_and(self.image, self.image, mask = self.mask)

def numberTemplate(filePath):
	name = filePath.split("/")[-1].split(".")[0]
	return TemplateWithTransparency(filePath, name)