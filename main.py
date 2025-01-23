import requests
import time
from pytweening import easeInOutSine


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


def get_credential_from_file(file_name: str, credential_name: str) -> str:
    try:
        with open(file_name, "r") as f:
            return f.readline().strip()
    except FileNotFoundError:
        print(f"{credential_name} not found. Please save your {credential_name} to `{file_name}`")
        exit(1)


def fetch_coordinates(api_key: str) -> tuple[float, float]:
    city = get_credential_from_file("LOCATION.txt", "City")
    geocoding_response = requests.get(f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={api_key}")
    try:
        location = geocoding_response.json()[0]
    except KeyError:
        print("Could not geolocate your location. Please try a different city.")
        exit(1)
    except IndexError:
        print("Could not geolocate your location. Please try a different city.")
        exit(1)

    if location.get("state"):
        print(f"Location: {location['name']}, {location['state']}, {location['country']}")
    else:
        print(f"Location: {location['name']}, {location['country']}")

    return location["lat"], location["lon"]


def fetch_weather(api_key: str, latitude: float, longitude: float) -> str:
    weather_response = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}"
    )
    weather_icon = weather_response.json().get("weather", [{}])[0].get("icon", "Unknown")[:2]
    return weather_icon


def tween_colours(colour_1: tuple[int, int, int], colour_2: tuple[int, int, int]) -> tuple[int, int, int]:
    """Calculate what colour should be shown at this point in time."""
    def remap(x: float, in_min: int, in_max: int, out_min: int, out_max: int) -> float:
        """Re-map a number `x` in the range of `in_min` to `in_max` to the range of `out_min` to `out_max`."""
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    cycle_time_ms = (time.time_ns() / 1000000) % 4000
    if cycle_time_ms / 2 >= 2000:
        cycle_time_ms -= 2000
        r1, g1, b1 = colour_1
        r2, g2, b2 = colour_2
    else:
        r1, g1, b1 = colour_2
        r2, g2, b2 = colour_1

    cycle_time_tweened = easeInOutSine(cycle_time_ms/2000)

    new_r = int(remap(cycle_time_tweened, 0, 1, r1, r2))
    new_g = int(remap(cycle_time_tweened, 0, 1, g1, g2))
    new_b = int(remap(cycle_time_tweened, 0, 1, b1, b2))

    return new_r, new_g, new_b



def main():
    api_key = get_credential_from_file("API_KEY.txt", "API key")
    latitude, longitude = fetch_coordinates(api_key)
    icon = fetch_weather(api_key, latitude, longitude)
    colours = CONDITION_COLOURS.get(icon, ((0, 0, 0), (255, 255, 255)))

    while True:
        print(tween_colours(*colours))
        time.sleep(0.1)


if __name__ == "__main__":
    main()
