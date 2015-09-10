from pprint import pprint
import cv2
import json

def potentialROIFactoryFactory(width, height):
	return lambda borderThickness: (
	    lambda xl,xh,yl,yh: PotentialROI(xl,xh,yl,yh,width,height+2*borderThickness,borderThickness))

class ROI:
	def setup(self, xlow, xhigh, ylow, yhigh, w,h, borderTop, borderBottom=-1):
		if borderBottom == -1:
			borderBottom = borderTop
		self.xlow = xlow
		self.xhigh = xhigh
		self.ylow = ylow
		self.yhigh = yhigh
		self.borderTop = borderTop
		self.borderBottom = borderBottom
		self.width = w
		self.height = h

	def scopeImage(self, meleeImage):
		meleeImage.setBorderVert(self.borderTop, self.borderBottom)
		return cv2.resize(meleeImage.image[self.ylow:self.yhigh, self.xlow:self.xhigh], (640,480))

	def __eq__(self, other):
		try:
			return ((self.xlow == other.xlow) and 
			        (self.xhigh == other.xhigh) and 
			        (self.ylow - self.borderBottom == other.ylow - other.borderBottom) and 
			        (self.yhigh - self.borderBottom == other.yhigh - other.borderBottom))
		except:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash("{0}.{1}.{2}.{3}".format(self.xlow, self.xhigh, 
		                                     self.ylow - self.borderBottom, 
		                                     self.yhigh - self.borderBottom))

	def toJson(self, tournamentId):
		return json.dumps({"roi": {
			"xlow": int(self.xlow),
			"xhigh": int(self.xhigh),
			"ylow": int(self.ylow),
			"yhigh": int(self.yhigh),
			"bordertop": int(self.borderTop),
			"borderbottom": int(self.borderBottom),
			"width": int(self.width),
			"height": int(self.height),
			"tournament_id": int(tournamentId)
			}})


class PotentialROI(ROI):
	def __init__(self, xlow, xhigh, ylow, yhigh, w,h, borderThickness):
		self.setup(xlow, xhigh, ylow, yhigh, w,h, borderThickness)
		self.ylrange = range(0, ylow + 3)
		self.yhrange = range(yhigh - 3, h)
		self.matchesFound = 0
		self.subROIs = [SubROI(xlow, xhigh, yl, yh, w,h,
		                       borderThickness) for yl in self.ylrange
		                                        for yh in self.yhrange]

	def rangeMaker(self, midPoint, reach, lowerLimit, upperLimit):
		return range(max(lowerLimit, midPoint - reach), 
		             min(upperLimit, midPoint + reach))

class SubROI(ROI):
	def __init__(self, xlow, xhigh, ylow, yhigh, w,h, borderThickness):
		self.setup(xlow, xhigh, ylow, yhigh, w,h, borderThickness)
		self.matchSum = [0.0, 0.0, 0.0]

	def matchSumAvg(self, foundCount):
		total = 0.0
		for i, count in enumerate(foundCount):
			if count > 0:
				total += self.matchSum[i] / count
		return total