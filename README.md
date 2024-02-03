# Weather station

Weather station based on Raspberry Pi PicoW.

Displays:

- In-doors temperature and humidity via DHT11
- Temperature, humidity and probability of rain outside
  via the [open-meteo API](https://open-meteo.com/en/docs)

## Installation

1. Download and install [Thonny](https://thonny.org/)
2. Create `src/secrets.py` with the following content:

```python
LAT = ...  # your latitude
LONG = ...  # your longitude
ssid = ...  # ssid of your wifi network
password = ... # password to your wifi network
```

3. Copy the contents of `src` to your RaspberryPi PicoW board using Thonny

## Hardware components

- RaspberryPi PicoW
- DHT11 temperature & humidity sensor
- TM1638 4-digits 7-segments display
