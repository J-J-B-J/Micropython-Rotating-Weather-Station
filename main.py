import requests


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
    weather_descriptor = weather_response.json().get("weather", [{}])[0].get("main", "Unknown")
    return weather_descriptor


def main():
    api_key = get_credential_from_file("API_KEY.txt", "API key")
    latitude, longitude = fetch_coordinates(api_key)
    descriptor = fetch_weather(api_key, latitude, longitude)
    if descriptor == "Unknown":
        print("Could not find your weather. Please try again later.")
    elif descriptor == "Clear":
        print("Clear skies right now.")
    elif descriptor == "Clouds" or descriptor == "Atmosphere":
        print("It's a little cloudy at the moment.")
    else:
        print("It's currently raining.")


if __name__ == "__main__":
    main()
