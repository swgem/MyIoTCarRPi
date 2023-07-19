#!/usr/bin/env python

import pyrebase
from time import sleep

exec(open("private-firebase-config.py").read())

firebase = pyrebase.initialize_app(config)

print("Process started. Press CTRL+C to exit")

while True:
	database = firebase.database()
	direction = database.child("forward").get().val()
	if direction:
		print("Andando para frente")
	else:
		print("Andando para trás")
	sleep(5.0)
