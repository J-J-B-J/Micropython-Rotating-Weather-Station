import time
import neopixel
import machine
from json import loads
import network
import socket
from math import cos, pi
from sys import exit


CONDITION_COLOURS = {
    "01": (
        (255, 255, 0),
        (255, 200, 0)
    ),
    "02": (
        (255, 255, 0),
        (180, 180, 180)
    ),
    "03": (
        (255, 255, 255),
        (180, 180, 180)
    ),
    "04": (
        (105, 105, 105),
        (180, 180, 180)
    ),
    "09": (
        (108, 108, 184),
        (180, 180, 180)
    ),
    "10": (
        (108, 108, 184),
        (105, 105, 105)
    ),
    "11": (
        (255, 255, 128),
        (105, 105, 105)
    ),
    "13": (
        (194, 194, 255),
        (255, 255, 255)
    ),
    "50": (
        (255, 255, 255),
        (180, 180, 180)
    ),
    "Un": (  # Unknown
        (255, 0, 0),
        (0, 0, 0)
    )
}


def sine_tween(n):
  return -0.5 * (cos(pi * n) - 1)


def get_credential_from_file(file_name: str, credential_name: str) -> str:
    try:
        with open(file_name, "r") as f:
            return f.readline().strip()
    except:
        print(f"{credential_name} not found. Please save your {credential_name} to `{file_name}`")
        exit(1)


def connect_to_wifi() -> None:
    wlan = network.WLAN(network.WLAN.IF_STA)
    wlan.active(True)
    wlan.connect(
        get_credential_from_file("SSID.txt", "Wi-Fi SSID"),
        get_credential_from_file("PASSWORD.txt", "Wi-Fi Password"),
    )
    while not wlan.isconnected():
        pass
    print(f"Connected to Wi-Fi with IP address {wlan.ipconfig('addr4')[0]}")


# This function is from https://github.com/micropython/micropython/blob/master/examples/network/http_client.py
def make_request(url, addr_family=0, use_stream=False) -> str:
    # `addr_family` selects IPv4 vs IPv6: 0 means either, or use
    # socket.AF_INET or socket.AF_INET6 to select a particular one.
    # Split the given URL into components.
    proto, _, host, path = [x.encode() for x in url.split("/", 3)]

    # Lookup the server address, for the given family and socket type.
    ai = socket.getaddrinfo(host, 80, addr_family, socket.SOCK_STREAM)

    # Select the first address.
    ai = ai[0]

    # Create a socket with the server's family, type and proto.
    s = socket.socket(ai[0], ai[1], ai[2])

    # Connect to the server.
    addr = ai[-1]
    s.connect(addr)

    try:
        # Send request and read response.
        request = b"GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n" % (path, host)
        if use_stream:
            # MicroPython socket objects support stream (aka file) interface
            # directly, but the line below is needed for CPython.
            s = s.makefile("rwb", 0)
            s.write(request)
            return s.read().decode().split("\r\n")[-1]
        else:
            s.send(request)
            return s.recv(8192).decode().split("\r\n")[-1]
    finally:
        # Close the socket.
        s.close()


def fetch_coordinates(api_key: str) -> tuple[float, float]:
    city = get_credential_from_file("LOCATION.txt", "City")
    geocoding_response = make_request(
        f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={api_key}",
        addr_family=socket.AF_INET,
    )
    try:
        location = loads(geocoding_response)[0]
    except:
        print("Could not geolocate your location. Please try a different city.")
        exit(1)

    if location.get("state"):
        print(f"Location: {location['name']}, {location['state']}, {location['country']}")
    else:
        print(f"Location: {location['name']}, {location['country']}")

    return location["lat"], location["lon"]


def fetch_weather(api_key: str, latitude: float, longitude: float) -> str:
    weather_response = make_request(
        f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}",
        addr_family=socket.AF_INET,
    )
    weather_icon = loads(weather_response).get("weather", [{}])[0].get("icon", "Unknown")[:2]
    return weather_icon


def tween_colours(colour_1: tuple[int, int, int], colour_2: tuple[int, int, int]) -> tuple[int, int, int]:
    """Calculate what colour should be shown at this point in time."""
    def remap(x: float, in_min: int, in_max: int, out_min: int, out_max: int) -> float:
        """Re-map a number `x` in the range of `in_min` to `in_max` to the range of `out_min` to `out_max`."""
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    cycle_time_ms = time.ticks_ms() % 4000
    if cycle_time_ms >= 2000:
        cycle_time_ms -= 2000
        r1, g1, b1 = colour_1
        r2, g2, b2 = colour_2
    else:
        r1, g1, b1 = colour_2
        r2, g2, b2 = colour_1

    cycle_time_tweened = sine_tween(cycle_time_ms / 2000)

    new_r = int(remap(cycle_time_tweened, 0, 1, r1, r2))
    new_g = int(remap(cycle_time_tweened, 0, 1, g1, g2))
    new_b = int(remap(cycle_time_tweened, 0, 1, b1, b2))

    return new_r, new_g, new_b



def main():
    led = neopixel.NeoPixel(machine.Pin(10), 1)
    led.fill((0, 255, 0))
    led.write()
    connect_to_wifi()
    api_key = get_credential_from_file("API_KEY.txt", "API key")
    latitude, longitude = fetch_coordinates(api_key)
    icon = fetch_weather(api_key, latitude, longitude)
    colour_1, colour_2 = CONDITION_COLOURS.get(icon, ((0, 0, 0), (255, 255, 255)))

    while True:
        led.fill(tween_colours(colour_1, colour_2))
        led.write()
        time.sleep_ms(50)


if __name__ == "__main__":
    main()
