
"""
based off of pwnagotchi's bettercaps file
"""
import requests
from requests.auth import HTTPBasicAuth
from subprocess import getoutput
from threading import Thread
from time import sleep
from os import system
from core.process_manager import process_manager

from core.logger import setup_logger
logger = setup_logger(__name__)

def decode(r):
    try:
        return r.json()
    except Exception as e:
        if r.status_code == 200:
            logger.error("error while decoding json: error='%s' resp='%s'" % (e, r.text))
        else:
            err = "error %d: %s" % (r.status_code, r.text.strip())
            raise Exception(err)
        return r.text


class Client(object):
    def __init__(
        self,
        hostname="localhost",
        scheme="http",
        port=8081,
        username="user",
        password="pass",
        iface="wlan0mon",
        start=True,
    ):
        self.hostname = hostname
        self.scheme = scheme
        self.port = port
        self.username = username
        self.password = password
        self.url = "%s://%s:%d/api" % (scheme, hostname, port)
        self.auth = HTTPBasicAuth(username, password)
        self.successful = None

        if start:
            Thread(
                target=self.start,
                daemon=True,
                kwargs={
                    "iface": iface,
                },
            ).start()

        Thread(target=self._wait_bettercap, daemon=True).start()

    def session(self):
        r = requests.get("%s/session" % self.url, auth=self.auth)
        return decode(r)

    def run(self, command):
        r = requests.post(
            "%s/session" % self.url, auth=self.auth, json={"cmd": command}
        )
        return decode(r)

    def start(self, iface: str = "wlan0mon"):
        #system("sudo bettercap --iface wlan0mon -eval 'set api.rest.address '0.0.0.0'; set api.rest.port 8081; set api.rest.username 'user'; set api.rest.password 'pass'; api.rest on;' -no-colors -no-history")
        bettercap_cmd = [
            'sudo', 'bettercap', '--iface', 'wlan0mon', 
            '-eval', "set api.rest.address '0.0.0.0'; set api.rest.port 8081; set api.rest.username 'user'; set api.rest.password 'pass'; api.rest on;",
            #"set http.server.address '0.0.0.0'; set http.server.port 80; set http.server.path '/usr/local/share/bettercap/ui/'; http.server on", 
            '-no-history', '-no-colors'
        ]
        process_manager.add_process(bettercap_cmd, name="BETTERCAP API", output_mode="file", filepath="/root/P4wnPet/logs/bettercap.log")


    def deauth(self, sta, throttle=0):
        try:
            self.run("wifi.deauth %s" % sta)
        except Exception as e:
            raise

        if throttle > 0:
            sleep(throttle)

    def associate(self, ap, throttle=0):
        try:
            self.run("wifi.assoc %s" % ap["mac"])
        except Exception as e:
            pass

        if throttle > 0:
            sleep(throttle)

    def getWifiJSON(self):
        r = requests.get("%s/session/wifi" % self.url, auth=self.auth)
        return decode(r)

    def clearWifi(self):
        return self.run("wifi.clear")

    def recon(self):
        self.run("set wifi.handshakes.aggregate false")
        return self.run("wifi.recon on")

    def hasHandshake(self, bssid):
        json = self.getWifiJSON()["aps"]

        for ap in json:
            if bssid == ap["mac"]:
                return ap["handshake"]

        return None

    def getPairs(self):
        json = self.getWifiJSON()

        # print(json)

        aps = {}

        for ap in json["aps"]:
            clientMacs = []

            apMac = ap["mac"]
            clients = ap["clients"]

            for client in clients:
                clientMacs.append([client["mac"], client["vendor"]])

            aps[apMac] = [
                ap["hostname"],
                ap["encryption"],
                {
                    "clients": clientMacs,
                    "freq": ap["frequency"],
                    "vendor": ap["vendor"],
                    "channel": ap["channel"],
                    "rssi": ap["rssi"],
                    "rfBands": ap["wps"]["RF Bands"]
                    if "RF Bands" in ap["wps"]
                    else None,
                    "ipv4": ap["ipv4"],
                    "ipv6": ap["ipv6"],
                    "dName": ap["wps"]["Device Name"]
                    if "Device Name" in ap["wps"]
                    else None,
                    "mName": ap["wps"]["Model Name"]
                    if "Model Name" in ap["wps"]
                    else None,
                    "mNumber": ap["wps"]["Model Number"]
                    if "Model Number" in ap["wps"]
                    else None,
                    "manufacturer": ap["wps"]["Manufacturer"]
                    if "Manufacturer" in ap["wps"]
                    else None,
                    "dType": ap["wps"]["Primary Device Type"]
                    if "Device Type" in ap["wps"]
                    else None,
                    "cfgMethods": ap["wps"]["Config Methods"]
                    if "Config Methods" in ap["wps"]
                    else None,
                },
            ]

        return aps

    def _wait_bettercap(self):
        for _ in range(5):
            try:
                requests.get("%s/session" % self.url, auth=self.auth)
                logger.info("[BCAP] bettercap avaialble")
                self.successful = True
            except Exception:
                logger.info("[BCAP] waiting for bettercap API to be available ...")
                sleep(1)

        self.successful = False

    def stop(self):
        getoutput("sudo pkill -f bettercap")
        # self.run("exit")
        while True:
            try:
                requests.get("%s/session" % self.url, auth=self.auth)
            except:
                return True
            sleep(1)