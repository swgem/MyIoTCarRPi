#!/usr/bin/env python

import pyrebase
import sys
import datetime
import signal
from gpiozero import Motor
from time import sleep

#---------------------------------------------------------------------------------------------------
# Global variables
#---------------------------------------------------------------------------------------------------

Sentry = True

car_motor1 = None
car_motor2 = None
car_direction = None
car_speed = None

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

def SignalHandler_SIGINT(SignalNumber,Frame):
	# Allow soft exit (wait for any running code before actually closing) and finish variables
	global Sentry
	Sentry = False

def update_car_movement():
	global car_motor1
	global car_motor2
	global car_direction
	global car_speed
	if car_direction:
		car_motor1.forward(car_speed)
		car_motor2.forward(car_speed)
	else:
		car_motor1.backward(car_speed)
		car_motor2.backward(car_speed)

def assert_speed(speed):
	if speed >= 0.0 and speed <= 1.0:
		return True
	else:
		return False

#---------------------------------------------------------------------------------------------------
# Code initialization
#---------------------------------------------------------------------------------------------------

signal.signal(signal.SIGINT, SignalHandler_SIGINT)

try:
	exec(open("private-firebase-config.py").read())
except FileNotFoundError:
	print("Error: File 'private-firebase-config.py' not found")
	sys.exit(-1)
firebase = pyrebase.initialize_app(config)
car_motor1 = Motor(6, 13)
car_motor2 = Motor(19, 26)

database = firebase.database()
car_direction = database.child("forward").get().val()
car_speed = database.child("speed").get().val()
if not assert_speed(car_speed):
	car_speed = 0.0
	print("Invalid car speed from database. Speed set to zero")
print("Car initial parameters:")
if car_direction:
	print("Direction: forward")
else:
	print("Direction: backward")
print("Speed: ", str(car_speed))

update_car_movement()

print("Process started. Press CTRL+C to exit")

#---------------------------------------------------------------------------------------------------
# Main loop
#---------------------------------------------------------------------------------------------------

while Sentry:
	timestamp_ini = datetime.datetime.now()
	
	database = firebase.database()

	new_direction = database.child("forward").get().val()
	if new_direction != car_direction:
		car_direction = new_direction
		if car_direction:
			print("Direction changed to forward")
		else:
			print("Direction changed to backward")
		update_car_movement()

	new_speed = database.child("speed").get().val()
	if new_speed != car_speed:
		if assert_speed(new_speed):
			car_speed = new_speed
			print("Speed changed to ", str(car_speed))
			update_car_movement()
		else:
			print("Invalid car speed from database. Speed was not updated")

	timestamp_end = datetime.datetime.now()
	if (timestamp_end - timestamp_ini).microseconds < 300000:
		sleep(0.3)

# Finishing execution
car_motor1.close()
car_motor2.close()
