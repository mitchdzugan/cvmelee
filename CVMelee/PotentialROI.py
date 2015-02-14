from pprint import pprint
import cv2

def potentialROIFactoryFactory(width, height):
	return lambda borderThickness: (
	    lambda xl,xh,yl,yh: PotentialROI(xl,xh,yl,yh,width,height+2*borderThickness,borderThickness))

class ROI:
	def setup(self, xlow, xhigh, ylow, yhigh, borderThickness):
		self.xlow = xlow
		self.xhigh = xhigh
		self.ylow = ylow
		self.yhigh = yhigh
		self.borderThickness = borderThickness

	def scopeImage(self, image):
		return cv2.resize(image[self.ylow:self.yhigh, self.xlow:self.xhigh], (1176,884))

	def __eq__(self, other):
		try:
			return ((self.xlow == other.xlow) and 
			        (self.xhigh == other.xhigh) and 
			        (self.ylow - self.borderThickness == other.ylow - other.borderThickness) and 
			        (self.yhigh - self.borderThickness == other.yhigh - other.borderThickness))
		except:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash("{0}.{1}.{2}.{3}".format(self.xlow, self.xhigh, 
		                                     self.ylow - self.borderThickness, 
		                                     self.yhigh - self.borderThickness))


class PotentialROI(ROI):
	def __init__(self, xlow, xhigh, ylow, yhigh, width, height, borderThickness):
		self.setup(xlow, xhigh, ylow, yhigh, borderThickness)
		self.ylrange = range(0, ylow + 3)
		self.yhrange = range(yhigh - 3, height)
		self.matchesFound = 0
		self.subROIs = [SubROI(xlow, xhigh, yl, yh, 
		                       borderThickness) for yl in self.ylrange
		                                        for yh in self.yhrange]

	def rangeMaker(self, midPoint, reach, lowerLimit, upperLimit):
		return range(max(lowerLimit, midPoint - reach), 
		             min(upperLimit, midPoint + reach))

class SubROI(ROI):
	def __init__(self, xlow, xhigh, ylow, yhigh, borderThickness):
		self.setup(xlow, xhigh, ylow, yhigh, borderThickness)
		self.matchesFound = 0
		self.mmatchesFound = 0
		self.matchSum = [0.0, 0.0, 0.0]

	def matchSumAvg(self, foundCount):
		total = 0.0
		for i, count in enumerate(foundCount):
			if count > 0:
				total += self.matchSum[i] / count
		return total