import math
import os
import time

from serpapi import GoogleSearch

interested_key = ["title", "gps_coordinates", "type", "address", "phone", "description", "website", "price", "rating", "operating_hours", "user_review"]
MAX_TRY = 10
def google_map(query,latitude,longitude):
    params = {
        "engine": "google_maps",
        "q": query,
        "ll": f"@{latitude},{longitude},19z",
        "type": "search",
        "google_domain": "google.com",
        "hl": "en",
        "api_key": os.environ["SERPAPI_API_KEY"]
    }
    for _ in range(MAX_TRY):
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
        except BaseException:
            time.sleep(0.3)
            continue
        break
    return results

def google_search(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": os.environ["SERPAPI_API_KEY"]
    }
    for _ in range(MAX_TRY):
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
        except BaseException:
            continue
        break
    return results

def distance_calculator(departure, destination):
    coord1 = [float(departure['latitude']), float(departure['longitude'])]
    coord2 = [float(destination['latitude']), float(destination['longitude'])]
    distance = _haversine_distance(coord1, coord2)
    return round(distance)


def _haversine_distance(coord1, coord2):
    # Radius of Earth in meters
    R = 6371000

    # Convert degrees to radians
    lat1, long1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, long2 = math.radians(coord2[0]), math.radians(coord2[1])

    # Differences in coordinates
    dlat = lat2 - lat1
    dlong = long2 - long1

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dlong / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance

def famous_sights(latitude, longitude):
    """The description is as follows:
    args:
        -place_info: The place_info argument is a dictionary that contains the following 3 parameters
        latitude: The latitude of the city where you want to find some famous attractions
        longitude: The longitude of the city where you want to find some famous attractions
        type: The type of famous sights
    return:
        some famous sights' location information and description
    functionality:
        If you want to search for detailed attraction information, you can call this tool.
    usage example:
        Tool: famous_sights
        Tool input: {"latitude": "xxx", "longitude": "xxx", "type": "xxx"}
    composition instructions:
        Before you call this tool, you should call geographic_places to acquire latitude and longitude
        After you call this tool and recommend_hotel tool, you should call distance_calculator tool multiple times to calculate the distance between hotel and each attraction.
    """
    sights = google_map("top sights", latitude, longitude)['local_results']
    ans = []
    for sight in sights:
        ans.append({k: v for k, v in sight.items() if k in interested_key})
    return ans


def geographic_places(city_name: str):
    """The description is as follows:
    args:
        -city_name: the name of your queried city
    return:
         geographic information about the city.
    functionality:
        This tool can be used to search for geographic information about a city. If you want to get the longitude, latitude and other geographic information about a city, you can call this tool.
    usage example:
        Tool: geographic_places
        Tool input: xxx
    composition instructions:
        You must call this tool to get the longitude and latitude before you call other tools that need latitude and longitude
    """
    'N,E positive'
    results = google_search(f"The latitude and longitude of {city_name}")
    answer = results['answer_box']['answer']
    latitude, longitude = answer.split(",")[0].strip(), answer.split(",")[1].strip()
    signed_latitude, signed_longitude = latitude.split(" ")[0][:-1], longitude.split(" ")[0][:-1]
    signed_latitude = "-"+signed_latitude if latitude.split(" ")[1] == "S"else signed_latitude
    signed_longitude = "-"+signed_longitude if longitude.split(" ")[1] == "W"else signed_longitude

    return {'lat': signed_latitude, 'lon': signed_longitude}

def famous_hotels(latitude, longitude):
    """The description is as follows:
    args:
        latitude: The latitude of the city where you want to book a hotel
        longitude: The longitude of the city where you want to book a hotel
        The input to this tool must be in this format:
        {"latitude": "xxx", "longitude": "xxx"}
    return:
        some famous hotels' location information and description
    functionality:
        If you want to search for detailed hotel information, you can call this tool.
    usage example:
        Tool: recommend_hotel
        Tool input: {"latitude": "xxx", "longitude": "xxx"}
    composition instructions:
        Before you call this tool, you can call geographic_places to acquire latitude and longitude.
        After you call this tool and famous_sights tool,you should call distance_calculator tool multiple times to calculate the distance between hotel and each attraction.
    """
    results = google_map("top hotels", latitude, longitude)
    all_results = []

    if 'ads' in results.keys():
        all_results += results['ads']
    if 'local_results' in results.keys():
        all_results += results['local_results']

    ans = []
    for hotel in all_results:
        ans.append({k: v for k, v in hotel.items() if k in interested_key})
    return ans

def famous_restaurants(latitude, longitude):
    """The description is as follows:
    args:
        latitude: The latitude of the city where you want to find a restaurant
        longitude: The longitude of the city where you want to find a restaurant
        The input to this tool must be in this format:
        {"latitude": "xxx", "longitude": "xxx"}
    return:
        some famous restaurants' location information and description
    functionality:
        If you want to search for detailed restaurants information, you can call this tool.
    usage example:
        Tool: recommend_restaurant
        Tool input: {"latitude": "xxx", "longitude": "xxx"}
    composition instructions:
        Before you call this tool, you can call geographic_places to acquire latitude and longitude.
        After you call this tool and recommend_hotel tool, you can call distance_calculator to calculate the distance between the restaurant and hotel.
    """
    results = google_map("top restaurants", latitude, longitude)['local_results']
    ans = []
    for restaurant in results:
        ans.append({k: v for k, v in restaurant.items() if k in interested_key})
    return ans

def recommend_flights(departure, destination):
    flight_info = google_search(f"The flights from {departure} to {destination}, skyscanner")['organic_results'][0]
    keys = ["title", "link", "snippet"]
    return {k: v for k, v in flight_info.items() if k in keys}

def recommend_cars(latitude, longitude) -> str:
    """The description is as follows:
    args:
        The input to this tool must be in this format:
        {"latitude": "xxx", "longitude": "xxx", "date": "YYYY-MM-DD"}
    return:
        car rental information
    functionality:
        This tool will return car rental information if you need to rent a car, you can call this tool
    usage example:
        Tool: rental_car
        Tool input: {"latitude": "xxx", "longitude": "xxx", "pick_up_date": "YYYY-MM-DD HH:MM:SS","drop_off_date": "YYYY-MM-DD HH:MM:SS"}
    composition instructions:
        Before you call this tool, you must call geographic_places to acquire the city's latitude and longitude.
        You need to rent a car to explore the city.
    """
    results = google_map("car rental", latitude, longitude)['local_results']
    ans = []
    for car in results:
        ans.append({k: v for k, v in car.items() if k in interested_key})
    return ans

