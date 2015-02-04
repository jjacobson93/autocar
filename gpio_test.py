from RPi import GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)


def turn_on():
	GPIO.output(7, True)

def turn_off():
	GPIO.output(7, False)


# GPIO.cleanup()


