import machine
import ntptime
import uasyncio
import urequests
import utime as time
from machine import I2C, Pin
from picozero import pico_led, pico_temp_sensor

import TM74HC595
from dht import DHT11, InvalidChecksum
from microdot_asyncio import Microdot
from web_server import Server, connect, open_socket, webpage
from secrets import LAT, LONG

N_REDRAW = 200
four_dgt = TM74HC595.Display(sclk=27, rclk=26, dio=22, n_segments=4)

dht_pin = Pin(2, Pin.OUT, Pin.PULL_DOWN)
sensor = DHT11(dht_pin)

API_URL = "https://api.open-meteo.com/v1/forecast"
current = ["temperature_2m", "relative_humidity_2m", "precipitation"]

opt = "&".join(
    [
        f"latitude={LAT}",
        f"longitude={LONG}",
        f"current={','.join(current)}",
        "hourly=precipitation_probability",
        "forecast_days=1",
    ]
)
url = f"{API_URL}?{opt}"

is_resp_ok = False
temp_outside = None
hum_outside = None
rain_outside = None
rain_proba = None


async def update_outside_weather(update_every_sec=15 * 60):
    resp = urequests.get(url)
    global is_resp_ok
    if resp.status_code != 200:
        is_resp_ok = False
        return
    is_resp_ok = True
    global temp_outside
    global hum_outside
    global rain_outside
    global rain_proba
    resp_json = resp.json()
    cur = resp_json["current"]
    hourly = resp_json["hourly"]
    temp_outside = float(cur["temperature_2m"])
    hum_outside = float(cur["relative_humidity_2m"])
    rain_outside = float(cur["precipitation"])

    now = cur["time"][:-2] + "00"  # round to previous hour
    print(now)
    print(hourly["time"])
    print(hourly["precipitation_probability"])
    ind = hourly["time"].index(now)
    rain_proba = hourly["precipitation_probability"][ind] / 100
    print("updated weather conditions")
    await uasyncio.sleep(update_every_sec)


async def show():
    while True:
        try:
            temp, hum = sensor.temperature, sensor.humidity
            print(temp_outside)
            await four_dgt.show("In__", n_redraw=N_REDRAW // 2)
            await four_dgt.show(f"{temp:.1f}z", n_redraw=N_REDRAW)
            await four_dgt.show(f"{hum:.0f}zo", n_redraw=N_REDRAW // 2)

            if is_resp_ok:
                await four_dgt.show("Out_", n_redraw=N_REDRAW // 2)
                await four_dgt.show(f"{temp_outside:.1f}z", n_redraw=N_REDRAW)
                await four_dgt.show(f"{hum_outside:.0f}zo", n_redraw=N_REDRAW // 2)
                await four_dgt.show(f"{rain_proba:.2f}P", n_redraw=N_REDRAW // 2)

        except Exception as e:
            print("error", e)
            await uasyncio.sleep(1)
            await four_dgt.show("Err", n_redraw=N_REDRAW / 4)


async def main(app):
    uasyncio.create_task(app.start_server(port=80))
    global task
    task = uasyncio.create_task(show())
    uasyncio.create_task(update_outside_weather())
    while True:
        await uasyncio.sleep(0)


app = Microdot()


@app.route("/")
def hello(_):
    return {"temp": sensor.temperature, "hum": sensor.humidity}


@app.route("/lighton")
def lighton(_):
    pico_led.on()
    return "OK"


@app.route("/lightoff")
def lightoff(_):
    pico_led.off()
    return "OK"


@app.route("/show")
async def show_route(request):
    text = request.args["text"]
    print(text)
    global task
    if task is not None:
        task.cancel()
    try:
        await four_dgt.show(text, n_redraw=N_REDRAW)
    finally:
        task = uasyncio.create_task(show())


uasyncio.run(main(app))
