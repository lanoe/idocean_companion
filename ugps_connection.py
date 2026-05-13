from http_connection import HttpConnection
import logging
logger = logging.getLogger(__name__)

# Code used from https://github.com/waterlinked/blueos-ugps-extension/blob/master/app/ugps_connection.py

class UgpsConnection(HttpConnection):
    """
    Interface with Water Linked UGPS G2 API (https://demo.waterlinked.com/swagger/)

    """

    def __init__(self, host: str = "https://demo.waterlinked.com"):
        HttpConnection.__init__(self, host)
        logger.info(f"{host}")
        self.version = "v1"

    def get_acoustic_locator_position(self):
        return super().get(f"/api/{self.version}/position/acoustic/filtered")
    
    def get_raw_acoustic_locator_position(self):
        return super().get(f"/api/{self.version}/position/acoustic/raw")

    def get_global_locator_position(self):
        return super().get(f"/api/{self.version}/position/global")

    def check_gps_compass_config(self) -> bool:
        """
        Get configuration GPS/Compass sources.
        """
        cfg = super().get(f"/api/{self.version}/config/generic")
        if cfg is None:
            logger.error("Unable to get ugps config")
            return False
        try:
            logger.info(f"Get configuration GPS = {cfg['gps']} and Compass = {cfg['compass']}")
            if cfg["gps"] != "external" or cfg["compass"] != "external" :
                logger.error(f"Update configuration for GPS/IMU to external !")
            #return super().put(f"/api/{self.version}/config/generic", cfg)
        except Exception:
            logger.error("Invalid ugps config format")
            return False
        return True

    def set_master_topside_position(self, lat, lon, cap):
        payload = dict(lat=lat, lon=lon, orientation=cap)
        return super().put(f"/api/{self.version}/external/master", payload) 

    def get_master_topside_position(self):
        return super().get(f"/api/{self.version}/position/master")

