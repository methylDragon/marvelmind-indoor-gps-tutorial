# marvelmind.py #

marvelmind.py includes small python class based on threading.Thread for receiving and parsing coordinates data from Marvelmind mobile beacon by USB/serial port.
example.py is an example of use.
Written by Alexander Rudykh (awesomequality@gmail.com)

[Download](https://bitbucket.org/marvelmind_robotics/marvelmind.py/get/default.zip)

## Attributes: ##

**tty** - serial port device name (physical or USB/virtual). It should be provided as an argument: 

  * /dev/ttyACM0 - typical for Linux

  * /dev/tty.usbmodem1451 - typical for Mac OS X


**baud** - baudrate. Should be match to baudrate of hedgehog-beacon

*Default value: 9600*


**maxvaluescount** - maximum count of measurements of coordinates stored in buffer

*Default value: 3*


**valuesUltrasoundPosition** - buffer of US position measures

**valuesImuRawData** - buffer of IMU raw measures (accelerometer, gyroscope, compass)

**valuesImuData** - buffer of IMU and US based measures (position, angular position (quaternion), velocities, accelerations) [x, y, z, qw, qx, qy, qz, vx, vy, vz, ax, ay, az, timestamp]


**debug** - debug flag which activate console output	

*Default value: False*


**pause** - pause flag. If True, class would not read serial data


**terminationRequired** - If True, thread would exit from main loop stop


## Methods: ##

**position(self)**

Return last measured data in array [x, y, z, timestamp]

**run(self)**

Main loop

**stop(self)**

Request to stop main loop and close serial port

**print_position(self)**

Print last measured data in default format

## Required libraries: ##

To prevent errors when installing crcmod module used in this script, use the following sequence of commands:

```
sudo apt-get install python-pip
sudo apt-get update
sudo apt-get install python-dev
sudo pip install crcmod
```