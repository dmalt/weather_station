import socket
from time import sleep
import time

import machine
import network
from picozero import pico_led, pico_temp_sensor
from secrets import ssid, password


def cet_time():
    year = time.localtime()[0]  # get current year
    HHMarch = time.mktime(
        (year, 3, (31 - (int(5 * year / 4 + 4)) % 7), 1, 0, 0, 0, 0, 0)
    )  # Time of March change to CEST
    HHOctober = time.mktime(
        (year, 10, (31 - (int(5 * year / 4 + 1)) % 7), 1, 0, 0, 0, 0, 0)
    )  # Time of October change to CET
    now = time.time()
    if now < HHMarch:  # we are before last sunday of march
        cet = time.localtime(now + 3600)  # CET:  UTC+1H
    elif now < HHOctober:  # we are before last sunday of october
        cet = time.localtime(now + 7200)  # CEST: UTC+2H
    else:  # we are after last sunday of october
        cet = time.localtime(now + 3600)  # CET:  UTC+1H
    return cet


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        print("Awaiting connection...")
        sleep(1)

    ip = wlan.ifconfig()[0]
    print(f"Connected on {ip}")
    return ip


def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection


def webpage(temperature, state):
    html = f"""
    <!DOCTYPE html>
    <html>
        <body>
            <form action="./lighton">
                <input type="submit" value="Light on" />
            </form>
            <form action="./lightoff">
                <input type="submit" value="Light off" />
            </form>
            <p>LED is {state}</p>
            <p>Temperature is {temperature}</p>
        </body>
    </html>
    """
    return str(html)


class Server:
    def __init__(self, connection):
        self.state = "OFF"
        pico_led.off()
        self.temperature = 0
        self.connection = connection

    def serve_step(self):
        client = self.connection.accept()[0]
        request = str(client.recv(1024))
        try:
            request = request.split()[1]
        except IndexError:
            pass
        if request == "/lighton?":
            pico_led.on()
            self.state = "ON"
        elif request == "/lightoff?":
            pico_led.off()
            self.state = "OFF"
        html = webpage(self.temperature, self.state)
        self.temperature = pico_temp_sensor.temp
        client.send(html)
        client.close()


def set_time():
    NTP_DELTA = 2208988800
    host = "pool.ntp.org"

    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    t = val - NTP_DELTA
    tm = time.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
