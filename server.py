from flask import Flask, request, render_template, jsonify, Response
# import turn as autocar
from threading import Thread, Event
from math import pi, sqrt, atan, cos, sin
import time

class Dumb:
	def __getattr__(self, k):
		return lambda: 1

autocar = Dumb()

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["PROPAGATE_EXCEPTIONS"] = True

map_data = {}
curr = None

SCALE = 1
BUFFER = 0 #width of the car in inches
INF = float('inf')


# instructions
FORWARD = 0
PIVOT = 1
PIVOT_LEFT = 2
PIVOT_RIGHT = 3

DRIVE_SPEED = SCALE * 13.5 # size of scale per second
LEFT_PIVOT_SPEED = 16/7.0 * pi # radians per second
RIGHT_PIVOT_SPEED = LEFT_PIVOT_SPEED # radians per second

class StoppableThread(Thread):
	def __init__(self, *args, **kwargs):
		super(StoppableThread, self).__init__(*args, **kwargs)
		self._stop = Event()

	def stop(self):
		map_data["stopped"] = True
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

@app.route("/", methods=["GET"])
def index():
	return render_template("index.html")

@app.route("/2", methods=["GET"])
def page2():
	return render_template("page2.html", waypoints=map_data.get("waypoints", []))

@app.route("/print", methods=["GET"])
def pprint(stdout=False):
	if map_data.get("graph"):
		output = ''
		for j in range(len(map_data["graph"]) - 1, -1, -1):
			s = ''
			for i in range(len(map_data["graph"][j])):
				if map_data["x"] == i and map_data["y"] == j:
					s += 'o'
				elif map_data["graph"][j][i]:
					s += "X"
				elif (i, j) in map_data["waypoints"]:
					s += "#"
				elif (i, j) in map_data["path"]:
					s += "$"
				else:
					s += "-"
			output += s + ('<br>' if not stdout else '\n')

		if not stdout:
			return "<html><body style='font-family:monospace'>" + output +\
				   "<br>Waypoints: " + str(map_data["waypoints"]) +\
				   "<br>Path: " + str(map_data["path"]) +\
				   "<br>Instructions: " + str(map_data["instr"]) +\
				   "</body></html>"
		else:
			return output +\
				   "\nPosition: ({}, {})".format(map_data["x"], map_data["y"]) +\
				   "\nHeading: " + str(map_data["heading"]) +\
				   "\nWaypoints: " + str(map_data["waypoints"]) +\
				   "\nPath: " + str(map_data["path"]) +\
				   "\nInstructions: " + str(map_data["instr"])
	else:
		return "No map"

@app.route("/setup", methods=["POST"])
def setup():
	map_data["run_thread"] = None
	map_data["stopped"] = True
	map_data["instr"] = []
	start_list = request.form.getlist("start[]")
	if start_list:
		x, y = map(int, start_list)
		map_data['x'] = x * SCALE
		map_data['y'] = y * SCALE
		map_data['heading'] = pi/2
	else:
		return "Start position not specified"

	obstacles = []
	i = 0
	while True:
		key = "obstacles[{}][]".format(i)
		l = request.form.getlist(key)
		if l:
			obstacles.append(map(int, l))
			i += 1
		else:
			break

	width = request.form.get("width")
	if width is None:
		return "Width is not specified"
	else:
		width = int(width)

	height = request.form.get("height")
	if height is None:
		return "Height is not specified"
	else:
		height = int(height)

	map_data["graph"] = [None]*height*SCALE
	for j in range(height*SCALE):
		map_data["graph"][j] = [False]*width*SCALE

	for (x,y,w,h) in obstacles:
		x = max(x - BUFFER, 0) * SCALE
		y = max(y - BUFFER, 0) * SCALE
		w = (w + 2*BUFFER) * SCALE
		h = (h + 2*BUFFER) * SCALE

		for i in xrange(x, min(x + w + 1, width*SCALE)):
			for j in xrange(y, min(y + h + 1, height*SCALE)):
				map_data["graph"][j][i] = True

	map_data['waypoints'] = []
	map_data['path'] = []

	return "Success: {}".format(map_data)

@app.route("/waypoint", methods=["GET", "POST", "DELETE"])
def waypoint():
	if request.method == "POST":
		# create a new waypoint
		x = int(request.form.get('x') or 0)/SCALE
		y = int(request.form.get('y') or 0)/SCALE
		if y < 0 or x < 0 or len(map_data["graph"]) < y or len(map_data["graph"][0]) < x or map_data["graph"][y][x]:
			return Response(response="Error: cannot put waypoint at ({}, {})".format(x, y), status=400)

		map_data['waypoints'].append((x, y))
		return "New waypoint: ({}, {})".format(x, y)
	elif request.method == "DELETE":
		stop()
		map_data['waypoints'] = []
		return "All waypoints deleted"
	elif request.method == "GET":
		return jsonify(waypoints=map_data["waypoints"])



@app.route("/start", methods=["POST"])
def start():
	print "Starting"
	map_data["stopped"] = False
	map_data["run_thread"] = StoppableThread(target=run_loop)
	map_data["run_thread"].start()
	return "Started"


def dijkstra(src, dest):
	vertices = map_data["graph"]

	# setup
	dist = {}
	previous = {}
	neighbors = {}
	q = set()
	for y in xrange(len(vertices)):
		for x in xrange(len(vertices[y])):
			dist[(x,y)] = INF
			previous[(x,y)] = None
			neighbors[(x,y)] = set()
			for j in range(max(y - 1, 0), min(y + 2, len(vertices))):				
				for i in range(max(x - 1, 0), min(x + 2, len(vertices[y]))):
					if not vertices[j][i] and (i, j) != (x, y):
						cost = 1.0 if i == x or j == y else sqrt(2.0)
						neighbors[(x,y)].add(((i,j), cost))
			q.add((x,y))

	dist[src] = 0
	while q:
		u = min(q, key=lambda vertex: dist[vertex])
		q.remove(u)
		if dist[u] == INF or u == dest:
			break
		for v, cost in neighbors[u]:
			alt = dist[u] + cost
			if alt < dist[v]:
				dist[v] = alt
				previous[v] = u

	s, u = [], dest
	while previous[u]:
		s.insert(0, u)
		u = previous[u]
	# s.insert(0, u)
	return s

def getangle(dx, dy):
	if dx != 0:
		return atan(dy*1.0/dx) + (pi/2 if dx < 0 else 0)

	return pi/2 if dy > 0 else -pi/2

def sq(x):
	return x**2

def translate(path):
	instr = []
	x, y = map_data['x'], map_data['y']
	heading = map_data['heading']

	if not path:
		return instr
	i, j = path[0]
	dx = i - x
	dy = j - y

	angle = getangle(dx, dy)

	instr.append((PIVOT, angle - heading))

	heading = angle

	prev_x = x
	prev_y = y
	for i, j in path[1:]:
		dx = i - x
		dy = j - y
		angle = getangle(dx, dy)
		if angle != heading:
			instr.append((FORWARD, sqrt(sq(x - prev_x) + sq(y - prev_y))))
			instr.append((PIVOT, angle - heading))
			heading = angle
			prev_x = x
			prev_y = y

		x = i
		y = j

	if prev_x != x or prev_y != y:
		instr.append((FORWARD, sqrt(sq(x - prev_x) + sq(y - prev_y))))

	return instr

SLEEP_TIME = 0.01
map_data["curr_time"] = time.time()

# def wait(amount):
# 	while not map_data["stopped"] and amount > 0:
# 		time.sleep(SLEEP_TIME)
# 		amount -= SLEEP_TIME

def drive(instr):
	for (i, amount) in instr:
		# map_data["curr_time"] = time.time()
		if i == FORWARD:
			map_data["curr_instr"] = FORWARD
			map_data["curr_speed"] = DRIVE_SPEED
			autocar.forward()
		elif i == PIVOT:
			if amount < 0:
				map_data["curr_instr"] = PIVOT_RIGHT
				# map_data["curr_time"] = time.time()
				autocar.pivot_right()
				map_data["curr_speed"] = RIGHT_PIVOT_SPEED
			else:
				map_data["curr_instr"] = PIVOT_LEFT
				# map_data["curr_time"] = time.time()
				autocar.pivot_left()
				map_data["curr_speed"] = LEFT_PIVOT_SPEED

		time.sleep(abs(amount)/map_data["curr_speed"])
		autocar.stop()
		if map_data["curr_instr"] == FORWARD:
			map_data["x"] += amount * cos(map_data["heading"])
			map_data["y"] += amount * sin(map_data["heading"])
		elif map_data["curr_instr"] == PIVOT_LEFT:
			map_data["heading"] += amount
			map_data["heading"] %= 2*pi
		elif map_data["curr_instr"] == PIVOT_RIGHT:
			map_data["heading"] += amount
			map_data["heading"] %= 2*pi
		if map_data["run_thread"].stopped():
			return False
		print pprint(True)

	return True

def run_loop():
	try:
		waypoints = map_data["waypoints"]
		while waypoints:
			assert not map_data["run_thread"].stopped()
			next = waypoints[0]
			heading = map_data['heading']
			path = dijkstra((map_data['x'], map_data['y']), next)
			map_data["path"] = path
			instr = translate(path)
			map_data["instr"] = instr
			if drive(instr):
				map_data["x"], map_data["y"] = next
				waypoints.pop(0)

	except AssertionError, e:
		return 

def calc_pos():
	if map_data["curr_instr"] == FORWARD:
		dist = deltat * DRIVE_SPEED
		map_data["x"] += dist * cos(map_data["heading"])
		map_data["y"] += dist * sin(map_data["heading"])
	elif map_data["curr_instr"] == PIVOT_LEFT:
		map_data["heading"] += LEFT_PIVOT_SPEED
		map_data["heading"] %= 2*pi
	elif map_data["curr_instr"] == PIVOT_RIGHT:
		map_data["heading"] += RIGHT_PIVOT_SPEED
		map_data["heading"] %= 2*pi

	# print pprint(True)

@app.route("/stop", methods=["POST"])
def stop():
	print "Stopping"
	if map_data["run_thread"]:
		map_data["run_thread"].stop()
		map_data["run_thread"].join()

	map_data["path"] = []
	map_data["instr"] = []
	autocar.stop()
	return "Stopped car"

@app.route("/turn-left")
def turn_left():
	print "Turning left"
	autocar.turn_left()
	return "Turned left"

@app.route("/turn-right")
def turn_right():
	print "Turning right"
	autocar.turn_right()
	return "Turned right"

@app.route("/test")
def test():
	return "Test"

@app.route("/forward")
def forward():
	n = float(request.args.get('n'))
	autocar.forward()
	time.sleep(n/DRIVE_SPEED)
	autocar.stop()
	return "Done"

@app.route("/pivot_left")
def pivot_left():
	n = float(request.args.get('n'))/180*pi
	autocar.pivot_left()
	time.sleep(abs(n)/LEFT_PIVOT_SPEED)
	autocar.stop()
	return "Done"

@app.route("/pivot_right")
def pivot_right():
	n = float(request.args.get('n'))/180*pi
	autocar.pivot_right()
	time.sleep(abs(n)/RIGHT_PIVOT_SPEED)
	autocar.stop()
	return "Done"

@app.route("/test-dijkstra")
def test_dijkstra():
	map_data["path"] = []
	waypoints = map_data["waypoints"]
	x = map_data['x']
	y = map_data['y']
	while waypoints:
		next = waypoints[0]
		heading = map_data['heading']
		path = dijkstra((x, y), next)
		instr = translate(path)
		map_data["path"] += path
		print "instructions:", instr
		# drive(instr)
		x, y = next
		waypoints.pop(0)
	return pprint()
	# return "<html><body style='font-family:monospace'>" + str(path) + "</body></html>"

@app.route("/test-dijkstra2")
def test_dijkstra2():
	map_data["path"] = []
	x = int(request.args.get('x'))
	y = int(request.args.get('y'))
	path = dijkstra((map_data['x'], map_data['y']), (x, y))
	instr = translate(path)
	map_data["path"] = path
	map_data["instr"] = instr
	return pprint()

if __name__ == "__main__":
	app.run(port=8080, host='0.0.0.0')


