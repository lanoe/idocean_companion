from http_connection import HttpConnection
import logging
logger = logging.getLogger(__name__)

class MavlinkConnection(HttpConnection):
    """
    Interface with Mavlink Rest API (https://mavlink.io/en/messages/ardupilotmega.html#messages)
    
    """

    def __init__(self, host):
        HttpConnection.__init__(self, host)
        logger.info(f"{host}")
        self.path = "/mavlink/vehicles/1/components/1/messages"

    def get_position_orientation(self):
        data1 = super().get(f"{self.path}/GLOBAL_POSITION_INT")
        data2 = super().get(f"{self.path}/ATTITUDE")
        del data1['message']['type']
        del data2['message']['type']
        result = data1['message'] | data2['message']
        return result
