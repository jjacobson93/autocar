import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)

def stop():
	GPIO.output(7, False)
	GPIO.output(11, False)
	GPIO.output(12, False)
	GPIO.output(16, False)

def forward():
	stop()
	GPIO.output(7, True)
	GPIO.output(12, True)

def backward():
	stop()
	GPIO.output(11, True)
	GPIO.output(16, True)

def turn_left():
	stop()
	GPIO.output(12, True)

def turn_right():
	stop()
	GPIO.output(7, True)

def pivot_left():
	stop()
	GPIO.output(12, True)
	GPIO.output(11, True)

def pivot_right():
	stop()
	GPIO.output(7, True)
	GPIO.output(16, True)

def back_turn_left():
	stop()
	GPIO.output(11, True)

def back_turn_right():
	stop()
	GPIO.output(16, True)

def clear():
	GPIO.cleanup()



