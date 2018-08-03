import crcmod
import serial
import struct
import collections
import time
from threading import Thread
import math
import numpy as np

class MarvelmindHedge (Thread):
    def __init__ (self, tty="/dev/ttyACM0", baud=9600, maxvaluescount=3, debug=False, recieveLinearDataCallback=None, recieveAccelerometerDataCallback=None):
        self.tty = tty  # serial
        self.baud = baud  # baudrate
        self.debug = debug  # debug flag
        self._bufferSerialDeque = collections.deque(maxlen=255)  # serial buffer
        self.lastLinearValues = collections.deque(maxlen=maxvaluescount) # meas. buffer
        self.lastLinearUpdateTime = 0
        self.recieveLinearDataCallback = recieveLinearDataCallback
        self.lastImuValues = collections.deque(maxlen=maxvaluescount) # meas. buffer
        self.lastImuValuesHandled = collections.deque(maxlen=maxvaluescount) # meas. buffer
        self.recieveAccelerometerDataCallback = recieveAccelerometerDataCallback
        
        for x in range(0, 10):
            self.lastLinearValues.append([0]*5) # last measured positions and timestamps; [x, y, z, timestamp]
        
        self.pause = False
        self.terminationRequired = False
        self.serialPort = None
        
        ####### IMU HERE #########
        self.lastImuValues = collections.deque(maxlen=maxvaluescount)
        self.recieveAccelerometerDataCallback = recieveAccelerometerDataCallback
        for x in range(0, 10):
            self.lastImuValues.append([0]*13) # last measured positions and timestamps; [x, y, z, timestamp]
            self.lastImuValuesHandled.append([0]*13) # last measured positions and timestamps; [x, y, z, timestamp]
        ##########################

        Thread.__init__(self)

    def print_position(self):
        if (isinstance(self.position()[1], int)):
            print ("Hedge {:d}: X: {:d}, Y: {:d}, Z: {:d} at time T: {:.2f}".format(self.position()[0], self.position()[1], self.position()[2], self.position()[3], self.position()[4]/1000.0))
        else:
            print ("Hedge {:d}: X: {:.2f}, Y: {:.2f}, Z: {:.2f} at time T: {:.2f}".format(self.position()[0], self.position()[1], self.position()[2], self.position()[3], self.position()[4]/1000.0))
 
    def print_accelerometer(self):
        print ("aX: {:f}, aY: {:f}, aZ: {:f} at time T: {:.2f}".format(self.acceleration()[0], self.acceleration()[1], self.acceleration()[2], self.acceleration()[3]))

    def print_gyro_position(self):
        print ("p: {:f}, r: {:f}, y: {:f} at time T: {:.2f}".format(self.gyro_position()[0], self.gyro_position()[1], self.gyro_position()[2], self.gyro_position()[3]))

    def print_gyro_speed(self):
        print ("wp: {:f}, wr: {:f}, wy: {:f} at time T: {:.2f}".format(self.gyro_speed()[0], self.gyro_speed()[1], self.gyro_speed()[2], self.gyro_speed()[3]))

    def position(self):
        return list(self.lastLinearValues)[-1];
    
    def imuposition(self):
        return list(self.lastImuValues)[-1];

    def print_imuposition(self):
        # x, y, z, qw, qx, qy, qz, vx,vy,vz,ax,ay,az, timestamp
        print ('~~~ Hedge ~~~')
        print ("X: {:f}, Y: {:f}, Z: {:f}".format(self.imuposition()[0],self.imuposition()[1],self.imuposition()[2]))
        print ("Vx: {:f}, Vy: {:f}, Vz: {:f}".format(self.imuposition()[7],self.imuposition()[8],self.imuposition()[9]))
        print ("Ax: {:f}, Ay: {:f}, Az: {:f}".format(self.imuposition()[10],self.imuposition()[11],self.imuposition()[12]))
        print ("Qw: {:f}, Qx: {:f}, Qy: {:f}, Qz: {:f}".format(self.imuposition()[3],self.imuposition()[4],self.imuposition()[5],self.imuposition()[6]))
        print ("Timestamp: {:d}".format(self.imuposition()[13]))

    def gyro_position(self):
        return list(self.lastGyroValues)[-1];

    def gyro_speed(self):
        return list(self.lastGyroSpeedValues)[-1];
    
    def stop(self):
        self.terminationRequired = True
        print ("stopping")

    def run(self):      
        while (not self.terminationRequired):
            if (not self.pause):
                try:
                    if (self.serialPort is None):
                        self.serialPort = serial.Serial(self.tty, self.baud, timeout=3)
                    readChar = self.serialPort.read(1)
                    while (readChar is not None) and (readChar is not '') and (not self.terminationRequired):
                        self._bufferSerialDeque.append(readChar)
                        readChar = self.serialPort.read(1)
                        bufferList = list(self._bufferSerialDeque)
                        
                        strbuf = (b''.join(bufferList))
                        # print (strbuf.decode())
                        # strbuf = 'asd'

                        ### ULTRASOUND DATA HERE ###
                        pktHdrOffset = strbuf.find(b'\xff\x47')
                        if (pktHdrOffset >= 0 and len(bufferList) > pktHdrOffset + 4 and pktHdrOffset<220):
#                           print(bufferList)
                            isMmMessageDetected = False;
                            isCmMessageDetected = False;
                            isImuMessageDetected = False;
                            pktHdrOffsetCm = strbuf.find(b'\xff\x47\x01\x00')
                            pktHdrOffsetMm = strbuf.find(b'\xff\x47\x11\x00')
                            pktHdrOffsetImu = strbuf.find(b'\xff\x47\x05\x00')

                            if (pktHdrOffsetMm!=-1):
                                isMmMessageDetected = True
                                if (self.debug): print ('Message with mm-data was detected')
                            elif (pktHdrOffsetCm!=-1):
                                isCmMessageDetected = True
                                if (self.debug): print ('Message with cm-data was detected')
                            elif (pktHdrOffsetImu!=-1):
                                isImuMessageDetected = True
                                if (self.debug): print ('Message with imu-data was detected')
                            msgLen = ord(bufferList[pktHdrOffset + 4])
                            if (self.debug): print ('Message length: ', msgLen)
                            
                            # offset+header+message+crc
                            #print 'len of buffer: ', len(bufferList), '; len of msg: ', msgLen, '; offset: ', pktHdrOffset
                            try:
                                if (len(bufferList) > pktHdrOffset + 4 + msgLen + 2):
                                    usnCRC16 = 0
                                    if (isCmMessageDetected):
                                        usnTimestamp, usnX, usnY, usnZ, usnAdr, usnCRC16 = struct.unpack_from ('<LhhhxBxxxxH', strbuf, pktHdrOffset + 5)
                                    elif (isMmMessageDetected):
                                        usnTimestamp, usnX, usnY, usnZ, usnAdr, usnCRC16 = struct.unpack_from ('<LlllxBxxxxH', strbuf, pktHdrOffset + 5)
                                        # usnX = usnX/10.0
                                        # usnY = usnY/10.0
                                        # usnZ = usnZ/10.0
                                    elif (isImuMessageDetected):
                                        # ax, ay, az, angRateX, angRateY, angRateZ, x, y, z, angx, angy, angz, timestamp, usnCRC16 = struct.unpack_from ('<hhhhhhhhhhhhLxxxxH', strbuf, pktHdrOffset + 5)
                                        x, y, z, qw, qx, qy, qz, vx, vy, vz, ax, ay, az, timestamp, usnCRC16 = struct.unpack_from ('<hhhhhhhhhhhhhxxLH', strbuf, pktHdrOffset + 5)


                                    crc16 = crcmod.predefined.Crc('modbus')
                                    crc16.update(strbuf[ pktHdrOffset : pktHdrOffset + msgLen + 5 ])
                                    CRC_calc = int(crc16.hexdigest(), 16)

                                    if CRC_calc == usnCRC16:
                                        if (isMmMessageDetected or isCmMessageDetected):
                                            if (usnAdr==62 or usnAdr==10000):
                                                value = [usnAdr, usnX/1000.0, usnY/1000.0, usnZ/1000.0, usnTimestamp]
                                                self.lastLinearValues.append(value)
                                                # self.handleUS()
                                                print ("%-10.0f %-10.0f %-20.0f" % (usnX/1000.0, usnY/1000.0, usnZ/1000.0))
                                                if (self.recieveLinearDataCallback is not None):
                                                    self.recieveLinearDataCallback()
                                        elif (isImuMessageDetected):
                                            value = [x/1000.0, y/1000.0, z/1000.0, qw/10000.0, qx/10000.0, qy/10000.0, qz/10000.0, vx/1000.0, vy/1000.0, vz/1000.0, ax/1000.0,ay/1000.0,az/1000.0, timestamp]
                                            self.lastImuValues.append(value)
                                            # self.handleIMU()
                                            # print (x,y,z)
                                            # print ("%-5.0f %-5.0f %-10.0f %-5.0f %-5.0f %-10.0f %-5.0f %-5.0f %-10.0f %-5.0f %-5.0f %-10.0f %-5.0f" % (x,y,z,vx,vy,vz,ax,ay,az,qx, qy, qz, timestamp))

                                            if (self.recieveAccelerometerDataCallback is not None):
                                                self.recieveAccelerometerDataCallback()
                                    else:
                                        if self.debug:
                                            print ('\n*** CRC ERROR')

                                    if pktHdrOffset == -1:
                                        if self.debug:
                                            print ('\n*** ERROR: Marvelmind USNAV beacon packet header not found (check modem board or radio link)')
                                        continue
                                    elif pktHdrOffset >= 0:
                                        if self.debug:
                                            print ('\n>> Found USNAV beacon packet header at offset %d' % pktHdrOffset)
                                            # self.print_position()
                                    for x in range(0, pktHdrOffset + msgLen + 7):
                                        self._bufferSerialDeque.popleft()
                            except struct.error:
                                print ('smth wrong')
                except OSError:
                    if self.debug:
                        print ('\n*** ERROR: OS error (possibly serial port is not available)')
                    time.sleep(1)
                except serial.SerialException:
                    if self.debug:
                        print ('\n*** ERROR: serial port error (possibly beacon is reset, powered down or in sleep mode). Restarting reading process...')
                    self.serialPort = None
                    time.sleep(1)
            else: 
                time.sleep(1)
    
        if (self.serialPort is not None):
            self.serialPort.close()