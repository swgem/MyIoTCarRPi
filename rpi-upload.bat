@ECHO OFF

call ./private-upload-config.bat

scp ./my-iot-car.py swgem@%rpi-ip%:~/
ssh swgem@%rpi-ip% "sudo mv ~/my-iot-car.py %rpi-bin-path%/"
scp ./my-iot-car-pvt-firebase-cfg.yaml swgem@%rpi-ip%:~/
ssh swgem@%rpi-ip% "sudo mv ~/my-iot-car-pvt-firebase-cfg.yaml %rpi-cfg-path%/"
scp ./adc-0832-lib.py swgem@%rpi-ip%:~/
ssh swgem@%rpi-ip% "sudo mv ~/adc-0832-lib.py %rpi-bin-path%/"
scp ./my-iot-car-pin-map.yaml swgem@%rpi-ip%:~/
ssh swgem@%rpi-ip% "sudo mv ~/my-iot-car-pin-map.yaml %rpi-cfg-path%/"
ssh swgem@%rpi-ip% "chmod +x %rpi-bin-path%/my-iot-car.py"
ssh swgem@%rpi-ip% "chmod +x %rpi-bin-path%/adc-0832-lib.py"
