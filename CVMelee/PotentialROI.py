def potentialROIFactory(width, height):
	return lambda xl,xh,yl,yh,fs: PotentialROI(xl,xh,yl,yh,fs,width,height)

class PotentialROI:
	def __init__(self, xlow, xhigh, ylow, yhigh, frameSet, width, height):
		self.xlow = xlow
		self.xhigh = xhigh
		self.ylow = ylow
		self.yhigh = yhigh
		self.frameSet = frameSet
		self.subROIs = [
			SubROI(xl, xh, 
			       yl, yh) for xl in self.rangeMaker(xlow, 3, 0, width)
			               for xh in self.rangeMaker(xhigh, 3, 0, width)
			               for yl in self.rangeMaker(ylow, 3, 0, height)
			               for yh in self.rangeMaker(yhigh, 3, 0, height)]

	def rangeMaker(self, midPoint, reach, lowerLimit, upperLimit):
		return range(max(lowerLimit, midPoint - reach), 
		             min(upperLimit, midPoint + reach))

class SubROI:
	def __init__(self, xlow, xhigh, ylow, yhigh):
		self.xlow = xlow
		self.xhigh = xhigh
		self.ylow = ylow
		self.yhigh = yhigh
