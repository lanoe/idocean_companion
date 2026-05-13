import requests
import time
import logging
logger = logging.getLogger(__name__)

class HttpConnection:

    def __init__(self, host):
        self.host = host

    def get(self, path: str):
        """
        Helper to request with GET
        Returns the response object or None on failure
        """
        full_url = self.host + path
        logger.debug(f"Request url: {full_url}")
        response = None
        try:
            response = requests.get(full_url)
            if response.status_code == 200:
                logger.debug(f"Got response: {response.text}")
                if response.text == "None":
                    return None
                return response.json()
            else:
                logger.error(f"Get HTTP {full_url} Error: {response.status_code} {response.reason} {response.text}")
                return None
        except Exception as e:
            logger.error(f"Got exception: {e}")
            return None

    def post(self, path: str, json: object) -> bool:
        """
        Helper to request with POST
        Returns if request was successful
        """
        full_url = self.host + path
        logger.debug(f"Request url: {full_url} json: {json}")
        response = None
        try:
            response = requests.post(full_url, json=json)
            if response.status_code == 200:
                logger.debug(f"Got response: {response.reason}")
                return True
            else:
                logger.error(f"Post HTTP {full_url}: {response.status_code} {response.reason} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Got exception: {e}")
            return False
   
    def put(self, path: str, json: object) -> bool:
        """
        Helper to request with PUT
        Returns if request was successful
        """
        full_url = self.host + path
        logger.debug(f"Request url: {full_url} json: {json}")
        response = None
        try:
            response = requests.put(full_url, json=json)
            if response.status_code == 200:
                logger.debug(f"Got response: {response.reason}")
                return True
            else:
                logger.error(f"Put HTTP {full_url} : {response.status_code} {response.reason} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Got exception: {e}")
            return False

    def wait_for_connection(self, path: str=""):
        """
        Waits until the HTTP server is available
        Returns when it is found
        """
        full_url = self.host + path
        while True:
            logger.info(f"Scanning for {full_url} ....")
            try:
                requests.get(self.host + path, timeout=1)
                break
            except Exception as e:
                logger.error(f"Got {e} from {full_url}")
            time.sleep(5)
        logger.debug(f"Got response from {full_url}")
