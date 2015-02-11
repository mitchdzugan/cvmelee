from pprint import pprint

def potentialROIFactory(width, height):
	return lambda xl,xh,yl,yh,fs: PotentialROI(xl,xh,yl,yh,fs,width,height)

class PotentialROI:
	def __init__(self, xlow, xhigh, ylow, yhigh, frameSet, width, height):
		self.ylrange = self.rangeMaker(ylow, 3, 0, height)
		self.yhrange = self.rangeMaker(yhigh, 3, 0, height)
		self.matchesFound = 0
		self.xlow = xlow
		self.xhigh = xhigh
		self.ylow = ylow
		self.yhigh = yhigh
		self.frameSet = frameSet
		self.subROIs = [SubROI(xlow, xhigh, yl, yh) for yl in self.ylrange
		                                            for yh in self.yhrange]

	def rangeMaker(self, midPoint, reach, lowerLimit, upperLimit):
		return range(max(lowerLimit, midPoint - reach), 
		             min(upperLimit, midPoint + reach))

class SubROI:
	def __init__(self, xlow, xhigh, ylow, yhigh):
		self.matchSum = 0.0
		self.xlow = xlow
		self.xhigh = xhigh
		self.ylow = ylow
		self.yhigh = yhigh

	def __eq__(self, other):
		try:
			return self.xlow == other.xlow && self.xhigh == other.xhigh && 
			       self.ylow == other.ylow && self.yhigh == other.yhigh
		except:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return [self.xlow, self.xhigh, self.ylow, self.yhigh].__hash__()