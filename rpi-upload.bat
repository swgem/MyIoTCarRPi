@ECHO OFF

call ./private-upload-config.bat

scp ./my-iot-car.py swgem@%rpi-ip%:%rpi-files-path%
scp ./private-firebase-config.py swgem@%rpi-ip%:%rpi-files-path%
ssh swgem@%rpi-ip% "chmod +x %rpi-files-path%/my-iot-car.py"
ssh swgem@%rpi-ip% "chmod +x %rpi-files-path%/private-firebase-config.py"
