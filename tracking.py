#!/usr/bin/python

import os
import time
import signal
import sys
import argparse
import logging
logger = logging.getLogger(__name__)

from settings import Config
from mavlink_connection import MavlinkConnection
from ugps_connection import UgpsConnection
from qgc_connection import QgcConnection

from datetime import datetime

def signal_handler(sig, frame):
    print("Arrêt du script...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Code used from https://github.com/waterlinked/blueos-ugps-extension/blob/master/app/main.py

class TrackingCompanion:
    """
    Main class for the IDocean Companion (with Water Linked Underwater GPS and BlueBoat/Mavlink)
    """
    def __init__(self, args) -> None:
        self.mavlink = MavlinkConnection(host=args.mavlink_host)
        self.ugps = UgpsConnection(host=args.ugps_host)
        self.qgc = QgcConnection(ip=args.qgc_ip, port=14401)
        self.args = args
        # for console display
        self.display = ['global_locator_position', 'acoustic_locator_position', 'master_topside_position', 'mavlink_position']
        self.last_display = {msg: "" for msg in self.display}

    def initDisplay(self):
        # Efface l'écran et initialise l'affichage
        print("\033[H\033[J", end="")  # Efface tout l'écran
        print("\n".join(f"{msg:15}: " for msg in self.display))
        print("\033[{}A".format(len(self.display)), end="")  # Remonte le curseur

    def updateDisplay(self, msg, data):
        if data == None:
            self.last_display[msg] = "no data !"
        else:
            self.last_display[msg] = " | ".join(f"{k}: {v}" for k, v in data.items())
        line_index = self.display.index(msg) + 1
        print(f"\033[{line_index};1H\033[K{msg:15}: {self.last_display[msg]}", flush=True)

    def run(self) -> None:
        """ Startup of service and main loop"""

        logger.info("Starting IDocean Tracking Companion ...")
        print("Starting IDocean Tracking Companion ...")

        print("Wait for Mavlink ...")
        self.mavlink.wait_for_connection()
        print("Wait for ugps ...")
        self.ugps.wait_for_connection()
        
        logger.info("Running...")
        print("Running ...")

        self.ugps.check_gps_compass_config()

        update_period = 0.25
        last_get_position_update = 0.0
        last_set_master_update = 0.0

        self.initDisplay()
        
        try:
            while True:
                time.sleep(0.05)

                if time.time() > last_set_master_update + update_period:
                    last_set_master_update = time.time()

                    # Forwarding master position from mavlink to ugps
                    mavlink_position = self.mavlink.get_position_orientation()
                    self.updateDisplay('mavlink_position', mavlink_position)
                    self.ugps.set_master_topside_position(mavlink_position['lat']/1e7, mavlink_position['lon']/1e7, int(mavlink_position['yaw']%360)) 

                if time.time() > last_get_position_update + update_period:
                    last_get_position_update = time.time()

                    # Get locator position
                    global_locator_position = self.ugps.get_global_locator_position()
                    self.updateDisplay('global_locator_position', global_locator_position)
                    acoustic_locator_position = self.ugps.get_acoustic_locator_position()
                    self.updateDisplay('acoustic_locator_position', acoustic_locator_position)
                    master_topside_position = self.ugps.get_master_topside_position()
                    self.updateDisplay('master_topside_position', master_topside_position)

                    if self.args.qgc_ip != "" and time.time() > last_master_update + update_period:
                        # Forwarding topside position from upgs to qgc
                        self.qgc.send_position(global_locator_position)
                    #    self.qgc.send_position(master_topside_position)
                    
        except KeyboardInterrupt:
            logger.info("Stop")
            print("\nFin...")

def main():
    
    config = Config()
    masterIp = config.data['BlueOS MavLink']['IP']
    locatorIp = config.data['WaterLinked UGPS']['IP']
    qgcIp = config.data['QGroundControl']['IP']
    
    parser = argparse.ArgumentParser(description="IDocean Tracker Companion \
                                     with WaterLinked UGPS and BlueBoat/BlueOS/Mavlink.")
    parser.add_argument('--ugps_host', action="store", type=str, default="http://"+locatorIp,
                        help="Host address for UGPS API, e.g. http://192.168.2.94 or \
                            https://demo.waterlinked.com (Port not needed as default http)")
    parser.add_argument('--mavlink_host', action="store", type=str, default="http://"+masterIp,
                        help="Host address for Mavlink API, e.g. http://blueos.local:6040 \
                            or http://127.0.0.1:6040 or http://10.128.149.207:6040 (Port needed as non-default.)")
    parser.add_argument('--qgc_ip', action="store", type=str, default=qgcIp,
                        help="Host address to send NMEA frame to QGroundControl via UDP. Set empty \
                            string "" to not send any NMEA frame over UDP.")
    parser.add_argument('--logfile', action="store_true",
                        help="Store a logfile with timestamp as name.")
    args = parser.parse_args()

    if args.logfile or True:
        # Crée le dossier logs s'il n'existe pas
        os.makedirs("logs", exist_ok=True)
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename=f"logs/{now}_tracking.log", level=logging.INFO)

    service = TrackingCompanion(args)
    service.run()

if __name__ == "__main__":
    main()
