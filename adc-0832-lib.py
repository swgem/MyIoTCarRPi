#!/usr/bin/env python

from gpiozero import DigitalOutputDevice
from gpiozero import DigitalInputDevice
from time import sleep

#---------------------------------------------------------------------------------------------------
# Global variables
#---------------------------------------------------------------------------------------------------

initialized = False
cs_device = None
clk_device = None
ctl_device = None # 0832 DI pin
sig_device = None # 0832 DO pin

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

def set_adc_pins(cs_pin, clk_pin, ctl_pin, sig_pin):
    global cs_device
    global clk_device
    global ctl_device
    global sig_device
    global initialized
    if not initialized:
        cs_device  = DigitalOutputDevice(cs_pin, True, True)
        clk_device = DigitalOutputDevice(clk_pin)
        ctl_device = DigitalOutputDevice(ctl_pin)
        sig_device = DigitalInputDevice(sig_pin)
        initialized = True
    else:
        print("Cannot set adc pins if they are already set")

def clear_adc_pins():
    global initialized
    if initialized:
        cs_device.close()
        clk_device.close()
        ctl_device.close()
        sig_device.close()
    else:
        print("Cannot clear adc pins if they are already clear")

def tick_clk():
    global initialized
    if initialized:
        sleep(0.001)
        clk_device.on()
        sleep(0.001)
        clk_device.off()
        sleep(0.001)
    else:
        print("Canoot 'tick' clk if devices were not initialized")

def read_analog():
    global initialized
    if initialized == True:
        cs_device.off()

        ctl_device.on()
        tick_clk()
        # SIGDIF should be '1'
        tick_clk()
        ctl_device.off() # ODDSIGN should be '0'
        tick_clk()
        # no in or out data
        tick_clk()

        msb_first = 0
        lsb_first = 0

        msb_first = sig_device.value
        tick_clk()
        msb_first = msb_first << 1
        msb_first = msb_first | sig_device.value
        tick_clk()
        msb_first = msb_first << 1
        msb_first = msb_first | sig_device.value
        tick_clk()
        msb_first = msb_first << 1
        msb_first = msb_first | sig_device.value
        tick_clk()
        msb_first = msb_first << 1
        msb_first = msb_first | sig_device.value
        tick_clk()
        msb_first = msb_first << 1
        msb_first = msb_first | sig_device.value
        tick_clk()
        msb_first = msb_first << 1
        msb_first = msb_first | sig_device.value
        tick_clk()
        msb_first = msb_first << 1
        msb_first = msb_first | sig_device.value
        lsb_first = sig_device.value
        tick_clk()
        lsb_first = lsb_first | sig_device.value << 1
        tick_clk()
        lsb_first = lsb_first | sig_device.value << 2
        tick_clk()
        lsb_first = lsb_first | sig_device.value << 3
        tick_clk()
        lsb_first = lsb_first | sig_device.value << 4
        tick_clk()
        lsb_first = lsb_first | sig_device.value << 5
        tick_clk()
        lsb_first = lsb_first | sig_device.value << 6
        tick_clk()
        lsb_first = lsb_first | sig_device.value << 7
        
        cs_device.on()

        if msb_first == lsb_first:
            return msb_first / 255
        else:
            print("Invalid data retrieved")
    else:
        print("ADC pins were not set yet")
