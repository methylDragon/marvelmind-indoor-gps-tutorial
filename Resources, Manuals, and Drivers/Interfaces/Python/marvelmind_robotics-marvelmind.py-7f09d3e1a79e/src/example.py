from marvelmind import MarvelmindHedge
from time import sleep
import sys

def main():
    hedge = MarvelmindHedge(tty = "/dev/ttyACM0", adr=10, debug=False) # create MarvelmindHedge thread
    hedge.start() # start thread
    while True:
        try:
            sleep(1)
            # print (hedge.position()) # get last position and print
            hedge.print_position()
        except KeyboardInterrupt:
            hedge.stop()  # stop and close serial port
            sys.exit()
main()