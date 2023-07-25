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

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

def SignalHandler_SIGINT(SignalNumber,Frame):
	# Allow soft exit (wait for any running code before actually closing) and finish variables
	global Sentry
	Sentry = False

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
motor1 = Motor(6, 13)
motor2 = Motor(19, 26)
print("Process started. Press CTRL+C to exit")

#---------------------------------------------------------------------------------------------------
# Main loop
#---------------------------------------------------------------------------------------------------

while Sentry:
	timestamp_ini = datetime.datetime.now()
	database = firebase.database()
	direction = database.child("forward").get().val()
	if direction:
		print("Andando para frente")
	else:
		print("Andando para trás")
	timestamp_end = datetime.datetime.now()
	if (timestamp_end - timestamp_ini).microseconds < 300000:
		sleep(0.3)

# Finishing execution
motor1.close()
motor2.close()
