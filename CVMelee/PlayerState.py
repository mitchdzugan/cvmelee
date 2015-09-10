import json

class PlayerState:
	def __init__(self, i, port):
		self.port = port
		self.stocks = 4
		self.percent = 0
		self.percentList = [[0, 4, i]]
		self.ignoredMatchQueue = []
		self.framesOfConsecNones = 0
		self.won = False

	def matchToPercent(self, match, threshold):
		percent = None
		for j in range(3):
			if match[j]["Match"] > threshold:
				if percent == None:
					percent = 0
				percent += match[j]["Digit"] * 10**j
			else:
				break
		return percent

	def processPercent(self, percent, frame, depth = 0):
		if percent == self.percent:
			self.ignoredMatchQueue = []
			self.framesOfConsecNones = 0
		elif percent == None:
			self.framesOfConsecNones += 5
			self.ignoredMatchQueue.append(list(self.currentMatch))
		elif percent == 0:
			if self.framesOfConsecNones < 30:
				self.ignoredMatchQueue.append(list(self.currentMatch))
			else:
				self.stocks -= 1
				self.percent = 0
				self.percentList.append([0, self.stocks, frame])
				self.ignoredMatchQueue = []
			self.framesOfConsecNones = 0
		elif percent < self.percent or percent > self.percent + 100:
			self.framesOfConsecNones = 0
			self.ignoredMatchQueue.append(list(self.currentMatch))
			if len(self.ignoredMatchQueue) > 2 and depth == 0:
				percentSet = set([self.matchToPercent(match, 0.40) for match in self.ignoredMatchQueue[-3:]])
				if len(percentSet) == 1:
					self.ignoredMatchQueue.pop()
					self.processPercent(list(percentSet)[0], frame, 1)
		else:
			self.framesOfConsecNones = 0
			self.percent = percent
			self.percentList.append([percent, self.stocks, frame])
			self.ignoredMatchQueue = []

	def eventsToJson(self, rawGamePortInfoId):
		return [json.dumps({"event": {
			"raw_game_port_info_id": rawGamePortInfoId,
			"stocks": e[1],
			"percent": e[0],
			"timestamp": e[2]
			}}) for e in self.percentList]

	def toJson(self, rawGameId):
		return json.dumps({"raw_game_port_info": {
			"raw_game_id": rawGameId,
			"port": self.port,
			"won": self.won
			}})