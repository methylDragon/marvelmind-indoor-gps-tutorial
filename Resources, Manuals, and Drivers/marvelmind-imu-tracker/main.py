from marvelmind2modified3 import MarvelmindHedge
import numpy as np


def updateUSNavData():
    global plotter
    global hedge

    if (plotter.showus):
        plotter.data[-1]['a_size'] = 15
        plotter.addPointUltrasoundBase(hedge.position()[1:4])
        plotter.data[-1]['a_size'] = 25
    plotter.usdata.append([hedge.position()[1],hedge.position()[2],hedge.position()[3]])

def updateAccData():
    global plotter
    global hedge

    if (plotter.showimu):
        plotter.data[-1]['a_size'] = 15
        plotter.addPointMod1([hedge.lastImuValues[-1][0],hedge.lastImuValues[-1][1],hedge.lastImuValues[-1][2]])
        plotter.data[-1]['a_size'] = 25
    plotter.imudata.append([hedge.lastImuValues[-1][0],hedge.lastImuValues[-1][1],hedge.lastImuValues[-1][2]])

    if (len(plotter.data)>plotter.pointlimiter+len(plotter.datastatic)):
        plotter.data = plotter.data[-plotter.pointlimiter:]
        plotter.data = np.append(plotter.datastatic, plotter.data)

global hedge
hedge = MarvelmindHedge(tty="/dev/ttyACM0", recieveLinearDataCallback=updateUSNavData, recieveAccelerometerDataCallback = updateAccData, debug=False)  # create MarvelmindHedge thread recieveAccelerometerDataCallback=updateAccData

import plotter3d2
from vispy import app
global plotter
plotter = plotter3d2.Canvas()

hedge.start()
app.run()