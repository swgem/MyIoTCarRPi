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
# Macros
#---------------------------------------------------------------------------------------------------

CALIBRATION_LAST_STEP = 5.0

#---------------------------------------------------------------------------------------------------
# Global variables
#---------------------------------------------------------------------------------------------------

Sentry = True

car_cfg_auto_led = None
car_cfg_auto_led_hysteresis = None
car_cfg_ldr_threshold = None
car_cfg_motor_left_right_pin_inverted = None
car_cfg_motor_left_direction_pin_inverted = None
car_cfg_motor_right_direction_pin_inverted = None
car_cfg_servo_pin_inverted = None

car_calibration_step = None

car_dev_motor1 = None
car_dev_motor2 = None
car_dev_servo_steering = None
car_dev_led = None

car_direction = None
car_speed = None
car_steering_angle = None
car_ldr = None

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

def SignalHandler_SIGINT(SignalNumber,Frame):
	# Allow soft exit (wait for any running code before actually closing) and finish variables
	global Sentry
	Sentry = False

def download_firebase_car_config():
	global car_cfg_auto_led
	global car_cfg_auto_led_hysteresis
	global car_cfg_ldr_threshold
	global car_cfg_motor_left_right_pin_inverted
	global car_cfg_motor_left_direction_pin_inverted
	global car_cfg_motor_right_direction_pin_inverted
	global car_cfg_servo_pin_inverted

	new_car_cfg_auto_led = database.child("config").child("autoLed").get().val()
	if new_car_cfg_auto_led != car_cfg_auto_led:
		car_cfg_auto_led = new_car_cfg_auto_led
		if car_cfg_auto_led:
			print("CONFIG: LED is set to change automatically with LDR")
		else:
			print("CONFIG: LED is set to change manually")

	new_car_cfg_auto_led_hysteresis = database.child("config").child("autoLedHysteresis").get().val()
	if new_car_cfg_auto_led_hysteresis != car_cfg_auto_led_hysteresis:
		car_cfg_auto_led_hysteresis = new_car_cfg_auto_led_hysteresis
		print("CONFIG: Car LDR automatic change hysteresis changed to ", str(car_cfg_auto_led_hysteresis))

	new_car_cfg_ldr_threshold = database.child("config").child("ldrThreshold").get().val()
	if new_car_cfg_ldr_threshold != car_cfg_ldr_threshold:
		car_cfg_ldr_threshold = new_car_cfg_ldr_threshold
		print("CONFIG: Car LDR threshold changed to ", str(car_cfg_ldr_threshold))

	new_car_cfg_motor_left_right_pin_inverted = \
		database.child("config").child("motorLeftRightPinInverted").get().val()
	if new_car_cfg_motor_left_right_pin_inverted != car_cfg_motor_left_right_pin_inverted:
		car_cfg_motor_left_right_pin_inverted = new_car_cfg_motor_left_right_pin_inverted
		if car_cfg_motor_left_right_pin_inverted:
			print("CONFIG: Car motors 1 and 2 are inverted by hardware")
		else:
			print("CONFIG: Car motors 1 and 2 are not inverted by hardware")

	new_car_cfg_motor_left_direction_pin_inverted = \
		database.child("config").child("motorLeftDirectionPinInverted").get().val()
	if new_car_cfg_motor_left_direction_pin_inverted != car_cfg_motor_left_direction_pin_inverted:
		car_cfg_motor_left_direction_pin_inverted = new_car_cfg_motor_left_direction_pin_inverted
		if car_cfg_motor_left_direction_pin_inverted:
			print("CONFIG: Car left motor direction pins are inverted by hardware")
		else:
			print("CONFIG: Car left motor direction pins are not inverted by hardware")

	new_car_cfg_motor_right_direction_pin_inverted = \
		database.child("config").child("motorRightDirectionPinInverted").get().val()
	if new_car_cfg_motor_right_direction_pin_inverted != car_cfg_motor_right_direction_pin_inverted:
		car_cfg_motor_right_direction_pin_inverted = new_car_cfg_motor_right_direction_pin_inverted
		if car_cfg_motor_right_direction_pin_inverted:
			print("CONFIG: Car right motor direction pins are inverted by hardware")
		else:
			print("CONFIG: Car right motor direction pins are not inverted by hardware")

	new_car_cfg_servo_pin_inverted = database.child("config").child("servoPinInverted").get().val()
	if new_car_cfg_servo_pin_inverted != car_cfg_servo_pin_inverted:
		car_cfg_servo_pin_inverted = new_car_cfg_servo_pin_inverted
		if car_cfg_servo_pin_inverted:
			print("CONFIG: Car servo direction pins are inverted")
		else:
			print("CONFIG: Car servo direction pins are not inverted")

def read_car_ldr():
	global car_ldr

	try:
		car_ldr = round(read_analog(), 2)
	except:
		print("Invalid LDR analog reading")
	database.child("status").update({"ldr": car_ldr})

def update_car_led():
	global car_cfg_auto_led
	global car_cfg_auto_led_hysteresis
	global car_cfg_ldr_threshold
	global car_dev_led
	global car_ldr

	if car_cfg_auto_led:
		new_car_led = 1 if (car_ldr > car_cfg_ldr_threshold or \
							(car_dev_led.value == 1 and \
								car_ldr > (car_cfg_ldr_threshold - car_cfg_auto_led_hysteresis))) \
						else 0
		if new_car_led != car_dev_led.value:
			if new_car_led == 1:
				car_dev_led.on()
				database.child("status").update({"led": True})
				print("Car LED turned ON")
			else:
				car_dev_led.off()
				database.child("status").update({"led": False})
				print("Car LED turned OFF")
	else:
		new_car_led = 1 if database.child("status").child("led").get().val() else 0
		if new_car_led != car_dev_led.value:
			if new_car_led == 1:
				car_dev_led.on()
				print("Car LED turned ON")
			else:
				car_dev_led.off()
				print("Car LED turned OFF")

def download_car_calibration_step():
	global car_calibration_step
	new_car_calibration_step = database.child("status").child("calibrationStep").get().val()
	if new_car_calibration_step != car_calibration_step:
		if asset_calibration_step(new_car_calibration_step):
			car_calibration_step = new_car_calibration_step
			if car_calibration_step == 0.0:
				print("Calibration step set to 0. Running on regular mode")
			else:
				print("Calibration step set to ", str(car_calibration_step))
		else:
			print("Invalid calibration step from database. Calibration step was not updated")

def download_car_direction():
	global car_direction
	new_direction = database.child("status").child("forward").get().val()
	if new_direction != car_direction:
		car_direction = new_direction
		if car_direction:
			print("Direction changed to forward")
		else:
			print("Direction changed to backward")

def download_car_speed():
	global car_speed
	new_speed = database.child("status").child("speed").get().val()
	if new_speed != car_speed:
		if assert_speed(new_speed):
			car_speed = new_speed
			if car_speed == 0.0:
				print("Car stopped")
			else:
				print("Speed changed to ", str(car_speed))
		else:
			print("Invalid car speed from database. Speed was not updated")

def download_car_steering_angle():
	global car_steering_angle
	new_steering_angle = database.child("status").child("steeringAngle").get().val()
	if new_steering_angle != car_steering_angle:
		if assert_steering_angle(new_steering_angle):
			car_steering_angle = new_steering_angle
			print("Steering angle changed to ", str(car_steering_angle))
		else:
			print("Invalid car steering angle from database. Steering angle set to zero")

def update_car_movement():
	global car_calibration_step
	if car_calibration_step == 0:
			update_car_movement_step_0()
	elif car_calibration_step == 1:
			update_car_movement_step_1()
	elif car_calibration_step == 2:
			update_car_movement_step_2()
	elif car_calibration_step == 3:
			update_car_movement_step_3()
	elif car_calibration_step == 4:
			update_car_movement_step_4()
	elif car_calibration_step == 5:
			update_car_movement_step_5()

def update_car_movement_step_0():
	global car_cfg_motor_left_right_pin_inverted
	global car_cfg_motor_left_direction_pin_inverted
	global car_cfg_motor_right_direction_pin_inverted
	global car_cfg_servo_pin_inverted
	global car_dev_motor1
	global car_dev_motor2
	global car_dev_servo_steering
	global car_direction
	global car_speed

	car_motor_left = car_dev_motor1 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor2
	car_motor_right = car_dev_motor2 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor1

	car_motor_left_hw_forward = car_motor_left.forward if \
									not car_cfg_motor_left_direction_pin_inverted \
									else car_motor_left.backward
	car_motor_left_hw_backward = car_motor_left.backward if \
									not car_cfg_motor_left_direction_pin_inverted \
									else car_motor_left.forward

	car_motor_right_hw_forward = car_motor_right.forward if \
									not car_cfg_motor_right_direction_pin_inverted \
									else car_motor_right.backward
	car_motor_right_hw_backward = car_motor_right.backward if \
									not car_cfg_motor_right_direction_pin_inverted \
									else car_motor_right.forward

	if car_speed == 0:
		car_motor_left.stop()
		car_motor_right.stop()
	else:
		if car_direction: # Go right
			car_motor_left_hw_forward(car_speed)
			car_motor_right_hw_forward(car_speed)
		else: # Go left
			car_motor_left_hw_backward(car_speed)
			car_motor_right_hw_backward(car_speed)
	car_dev_servo_steering.value = car_steering_angle if not car_cfg_servo_pin_inverted \
								else (-1) * car_steering_angle

def update_car_movement_step_1():
	global car_cfg_motor_left_right_pin_inverted
	global car_cfg_servo_pin_inverted
	global car_dev_motor1
	global car_dev_motor2
	global car_dev_servo_steering

	car_motor_left = car_dev_motor1 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor2
	car_motor_right = car_dev_motor2 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor1

	car_dev_servo_steering.value = 0

	car_motor_left.forward(1.0)
	car_motor_right.stop()

def update_car_movement_step_2():
	global car_cfg_motor_left_right_pin_inverted
	global car_cfg_servo_pin_inverted
	global car_dev_motor1
	global car_dev_motor2
	global car_dev_servo_steering

	car_motor_left = car_dev_motor1 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor2
	car_motor_right = car_dev_motor2 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor1

	car_dev_servo_steering.value = 0

	car_motor_left.stop()
	car_motor_right.forward(1.0)

def update_car_movement_step_3():
	global car_cfg_motor_left_right_pin_inverted
	global car_cfg_motor_left_direction_pin_inverted
	global car_cfg_servo_pin_inverted
	global car_dev_motor1
	global car_dev_motor2
	global car_dev_servo_steering

	car_motor_left = car_dev_motor1 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor2
	car_motor_right = car_dev_motor2 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor1
	car_motor_left_hw_forward = car_motor_left.forward if \
									not car_cfg_motor_left_direction_pin_inverted \
									else car_motor_left.backward

	car_dev_servo_steering.value = 0

	car_motor_left_hw_forward(1.0)
	car_motor_right.stop()

def update_car_movement_step_4():
	global car_cfg_motor_left_right_pin_inverted
	global car_cfg_motor_right_direction_pin_inverted
	global car_cfg_servo_pin_inverted
	global car_dev_motor1
	global car_dev_motor2
	global car_dev_servo_steering

	car_motor_left = car_dev_motor1 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor2
	car_motor_right = car_dev_motor2 if not car_cfg_motor_left_right_pin_inverted \
						else car_dev_motor1
	car_motor_right_hw_forward = car_motor_right.forward if \
									not car_cfg_motor_right_direction_pin_inverted \
									else car_motor_right.backward

	car_dev_servo_steering.value = 0

	car_motor_left.stop()
	car_motor_right_hw_forward(1.0)

def update_car_movement_step_5():
	global car_cfg_servo_pin_inverted
	global car_dev_motor1
	global car_dev_motor2
	global car_dev_servo_steering

	car_dev_motor1.stop()
	car_dev_motor2.stop()
	car_dev_servo_steering.value = (-1) if not car_cfg_servo_pin_inverted \
								else (-1) * (-1)

def asset_calibration_step(calibration_step):
	if calibration_step >= 0.0 and calibration_step <= CALIBRATION_LAST_STEP:
		return True
	else:
		return False

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

car_dev_motor1_pin1 = pin_map['car_motor1_pin1']
car_dev_motor1_pin2 = pin_map['car_motor1_pin2']
car_dev_motor2_pin1 = pin_map['car_motor2_pin1']
car_dev_motor2_pin2 = pin_map['car_motor2_pin2']
car_dev_servo_steering_pin = pin_map['car_servo_steering_pin']
car_dev_ldr_cs_pin = pin_map['car_ldr_cs_pin']
car_dev_ldr_clk_pin = pin_map['car_ldr_clk_pin']
car_dev_ldr_ctl_pin = pin_map['car_ldr_ctl_pin']
car_dev_ldr_sig_pin = pin_map['car_ldr_sig_pin']
car_dev_led_pin = pin_map['car_led_pin']

config = {
	"apiKey": api_key,
	"authDomain": auth_domain,
	"databaseURL": database_URL,
	"storageBucket": storage_bucket
}
firebase = pyrebase.initialize_app(config)
car_dev_motor1 = Motor(car_dev_motor1_pin1, car_dev_motor1_pin2)
car_dev_motor2 = Motor(car_dev_motor2_pin1, car_dev_motor2_pin2)
car_dev_servo_steering_pin_factory = PiGPIOFactory()
car_dev_servo_steering = Servo(car_dev_servo_steering_pin, \
							   pin_factory=car_dev_servo_steering_pin_factory)

set_adc_pins(car_dev_ldr_cs_pin, car_dev_ldr_clk_pin, car_dev_ldr_ctl_pin, car_dev_ldr_sig_pin)

try:
	car_ldr = read_analog()
except:
	print("Invalid LDR analog reading")
car_dev_led = LED(car_dev_led_pin)

database = firebase.database()

print("--------------------")
download_firebase_car_config()
print("--------------------")
download_car_calibration_step()
download_car_direction()
download_car_speed()
download_car_steering_angle()
print("--------------------")

update_car_movement()

#---------------------------------------------------------------------------------------------------
# Main loop
#---------------------------------------------------------------------------------------------------

while Sentry:
	timestamp_ini = datetime.datetime.now()

	database = firebase.database()

	download_firebase_car_config()
	read_car_ldr()
	download_car_direction()
	download_car_speed()
	download_car_steering_angle()

	download_car_calibration_step()

	update_car_led()
	update_car_movement()

	timestamp_end = datetime.datetime.now()
	if (timestamp_end - timestamp_ini).microseconds < 300000:
		sleep(0.3)

# Finishing execution
car_dev_motor1.close()
car_dev_motor2.close()
car_dev_servo_steering.close()
car_dev_led.close()
clear_adc_pins()
