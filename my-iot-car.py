#!/usr/bin/env python

import pyrebase
import sys
import datetime
import signal
import yaml
from gpiozero import Motor
from gpiozero import Servo
from gpiozero import LED
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

#---------------------------------------------------------------------------------------------------
# Global variables
#---------------------------------------------------------------------------------------------------

Sentry = True

car_motor1 = None
car_motor2 = None
car_direction = None
car_speed = None
car_servo_steering = None
car_ldr = None
car_ldr_threshold = None
car_led = None
car_auto_led = None

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
	if car_speed == 0:
		car_motor1.stop()
		car_motor2.stop()
	else:
		if car_direction:
			car_motor1.forward(car_speed)
			car_motor2.forward(car_speed)
		else:
			car_motor1.backward(car_speed)
			car_motor2.backward(car_speed)
	car_servo_steering.value = (-1) * car_steering_angle

def assert_speed(speed):
	if speed >= 0.0 and speed <= 1.0:
		return True
	else:
		return False
	
def assert_steering_angle(steering_angle):
	if steering_angle >= -1.0 and steering_angle <= 1.0:
		return True
	else:
		return False

#---------------------------------------------------------------------------------------------------
# Code initialization
#---------------------------------------------------------------------------------------------------

print("Process started. Press CTRL+C to exit")

signal.signal(signal.SIGINT, SignalHandler_SIGINT)

sleep(1.0)

try:
	with open("/etc/my-iot-car-pvt-firebase-cfg.yaml", "r") as file:
		firebase_cfg = yaml.safe_load(file)
except FileNotFoundError:
	print("Error: File '/etc/my-iot-car-pvt-firebase-cfg.yaml' not found")
	sys.exit(-1)

try:
	with open("/etc/my-iot-car-pin-map.yaml", "r") as file:
		pin_map = yaml.safe_load(file)
except FileNotFoundError:
	print("Error: File '/etc/my-iot-car-pin-map.yaml' not found")
	sys.exit(-1)

try:
	exec(open("/usr/local/bin/adc-0832-lib.py").read())
except FileNotFoundError:
	print("Error: File '/usr/local/bin/adc-0832-lib.py' not found")
	sys.exit(-1)

api_key = firebase_cfg['api_key']
auth_domain = firebase_cfg['auth_domain']
database_URL = firebase_cfg['database_URL']
storage_bucket = firebase_cfg['storage_bucket']

car_motor1_pin1 = pin_map['car_motor1_pin1']
car_motor1_pin2 = pin_map['car_motor1_pin2']
car_motor2_pin1 = pin_map['car_motor2_pin1']
car_motor2_pin2 = pin_map['car_motor2_pin2']
car_servo_steering_pin = pin_map['car_servo_steering_pin']
car_ldr_cs_pin = pin_map['car_ldr_cs_pin']
car_ldr_clk_pin = pin_map['car_ldr_clk_pin']
car_ldr_ctl_pin = pin_map['car_ldr_ctl_pin']
car_ldr_sig_pin = pin_map['car_ldr_sig_pin']
car_led_pin = pin_map['car_led_pin']

config = {
	"apiKey": api_key,
	"authDomain": auth_domain,
	"databaseURL": database_URL,
	"storageBucket": storage_bucket
}
firebase = pyrebase.initialize_app(config)
car_motor1 = Motor(car_motor1_pin1, car_motor1_pin2)
car_motor2 = Motor(car_motor2_pin1, car_motor2_pin2)
car_servo_steering_pin_factory = PiGPIOFactory()
car_servo_steering = Servo(car_servo_steering_pin, pin_factory=car_servo_steering_pin_factory)

set_adc_pins(car_ldr_cs_pin, car_ldr_clk_pin, car_ldr_ctl_pin, car_ldr_sig_pin)
car_ldr = read_analog()
car_led = LED(car_led_pin)

database = firebase.database()
car_auto_led = database.child("config").child("autoLed").get().val()
car_ldr_threshold = database.child("config").child("ldrThreshold").get().val()
car_direction = database.child("status").child("forward").get().val()
car_speed = database.child("status").child("speed").get().val()
car_steering_angle = database.child("status").child("steeringAngle").get().val()

if not assert_speed(car_speed):
	car_speed = 0.0
	print("Invalid car speed from database. Speed set to zero")
if not assert_steering_angle(car_steering_angle):
	car_steering_angle = 0.0
	print("Invalid car steering angle from database. Steering angle set to zero")
print("--------------------")
print("Car initial parameters:")
if car_direction:
	print("Direction: forward")
else:
	print("Direction: backward")
print("Speed: ", str(car_speed))
print("Steering angle: ", str(car_speed))
print("LDR threshold: ", str(car_ldr_threshold))
if car_auto_led:
	print("LED is set to change automatically with LDR")
else:
	print("LED is set to change manually")
print("--------------------")

update_car_movement()

#---------------------------------------------------------------------------------------------------
# Main loop
#---------------------------------------------------------------------------------------------------

while Sentry:
	timestamp_ini = datetime.datetime.now()
	
	database = firebase.database()

	new_car_auto_led = database.child("config").child("autoLed").get().val()
	if new_car_auto_led != car_auto_led:
		car_auto_led = new_car_auto_led
		if car_auto_led:
			print("LED is set to change automatically with LDR")
		else:
			print("LED is set to change manually")
	new_car_ldr_threshold = database.child("config").child("ldrThreshold").get().val()
	if new_car_ldr_threshold != car_ldr_threshold:
		car_ldr_threshold = new_car_ldr_threshold
		print("Car LDR threshold changed to ", str(car_ldr_threshold))
	car_ldr = round(read_analog(), 2)
	database.child("status").update({"ldr": car_ldr})
	if car_auto_led:
		new_car_led = 1 if car_ldr > car_ldr_threshold else 0
		if new_car_led != car_led.value:
			if new_car_led == 1:
				car_led.on()
				database.child("status").update({"led": True})
				print("Car LED turned ON")
			else:
				car_led.off()
				database.child("status").update({"led": False})
				print("Car LED turned OFF")
	else:
		new_car_led = 1 if database.child("status").child("led").get().val() else 0
		if new_car_led != car_led.value:
			if new_car_led == 1:
				car_led.on()
				print("Car LED turned ON")
			else:
				car_led.off()
				print("Car LED turned OFF")

	new_direction = database.child("status").child("forward").get().val()
	if new_direction != car_direction:
		car_direction = new_direction
		if car_direction:
			print("Direction changed to forward")
		else:
			print("Direction changed to backward")
		update_car_movement()

	new_speed = database.child("status").child("speed").get().val()
	if new_speed != car_speed:
		if assert_speed(new_speed):
			car_speed = new_speed
			if car_speed == 0.0:
				print("Car stopped")
			else:
				print("Speed changed to ", str(car_speed))
			update_car_movement()
		else:
			print("Invalid car speed from database. Speed was not updated")

	new_steering_angle = database.child("status").child("steeringAngle").get().val()
	if new_steering_angle != car_steering_angle:
		if assert_steering_angle(new_steering_angle):
			car_steering_angle = new_steering_angle
			print("Steering angle changed to ", str(car_steering_angle))
			update_car_movement()
		else:
			print("Invalid car steering angle from database. Steering angle set to zero")

	timestamp_end = datetime.datetime.now()
	if (timestamp_end - timestamp_ini).microseconds < 300000:
		sleep(0.3)

# Finishing execution
car_motor1.close()
car_motor2.close()
car_servo_steering.close()
clear_adc_pins()
car_led.close()
