import cv2

class MeleeImage:
	def __init__(self, image, borderTop=0, borderBottom=0):
		self.image = image
		self.borderlessImage = image
		self.borderTop = 0
		self.borderBottom = 0
		self.setBorderVert(borderTop, borderBottom)

	def setBorderTop(self, borderTop):
		self.setBorderVert(borderTop, self.borderBottom)

	def setBorderTop(self, borderBottom):
		self.setBorderVert(self.borderTop, borderBottom)

	def setBothBorderVert(self, border):
		self.setBorderVert(border, border)

	def setBorderVert(self, borderTop, borderBottom):
		if (self.borderTop != borderTop or self.borderBottom != borderBottom):
			self.borderTop = borderTop
			self.borderBottom = borderBottom
			self.image = cv2.copyMakeBorder(self.borderlessImage,
			                                self.borderTop, self.borderBottom,
			                                0, 0, cv2.BORDER_CONSTANT, 0)