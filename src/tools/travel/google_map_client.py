import random
import time
import googlemaps
import os
import numpy as np
from src.tools.travel.serpAPI import recommend_flights
from src.utils.debug import log_info
import src.tools.travel.serpAPI as serpAPI
interested_key = ["title", "gps_coordinates", "type", "address", "phone", "description", "website", "price", "rating",
                  "operating_hours", "user_review", "formatted_address", "geometry", "name", "url"]
MAX_TRY = 10
OPEN_SERP_API = False

class google_map_client:
    def __init__(self, city_name="shanghai, china"):
        self.client = googlemaps.Client(key=os.environ["GOOGLEMAP_API_KEY"])
        self.city_name = city_name
    def geographic_places(self, city_name):
        i = 0
        while i < MAX_TRY:
            try:
                address_list = city_name.split(",")
                if len(address_list) == 3:
                    city, state, country = address_list
                    geo_info = self.client.geocode(address=city, components={"administrative_area": state, "country": country})
                else:
                    city, country = address_list
                    geo_info = self.client.geocode(address=city, components={"country": country})

                geo_info = geo_info[0]["geometry"]["location"]
                return {'latitude': geo_info['lat'], 'longitude': geo_info['lng']}
            except BaseException:
                i += 1
                time.sleep(1)

    def find_place(self, place_name):
        i = 0
        while i < MAX_TRY:
            try:
                place_id = self.client.find_place(place_name, 'textquery')
                raw_result = self.client.place(place_id['candidates'][0]['place_id'])["result"]
                result = {k: v for k, v in raw_result.items() if k in interested_key}
                geo_info = result.pop('geometry')['location']
                result['gps_coordinates'] = {'latitude': geo_info['lat'], 'longitude': geo_info['lng']}
                return result
            except BaseException:
                i += 1
                time.sleep(1)

    def geo_convert(self, geo):
        """This method convert array/dictionary-like geo information to tuple"""
        if isinstance(geo, list) or isinstance(geo, type(np.array(2))):
            geo = (geo[0], geo[1])
        elif isinstance(geo, dict):
            geo = (geo['latitude'], geo['longitude'])
        return geo

    def search_hotel(self, geo, radius=5000, keyword='hotels'):
        geo = self.geo_convert(geo)
        if OPEN_SERP_API:
            hotels = serpAPI.famous_hotels(geo[0], geo[1])
            if hotels is None or len(hotels) == 0:
                return None
            else:
                return hotels[0]

        else:
            hotels = self.places_nearby(geo, radius, keyword)
            if hotels is None or len(hotels) == 0:
                return None
            else:
                hotel_name = hotels[0]['name']
                return self.find_place(f"{hotel_name},{self.city_name}")

    def search_restaurants(self, geo, radius=2000, keyword='restaurants'):
        geo = self.geo_convert(geo)
        if OPEN_SERP_API:
            restaurants = serpAPI.famous_restaurants(geo[0], geo[1])
            if restaurants is None or len(restaurants) == 0:
                return None
            else:
                return restaurants[0]
        else:
            restaurants = self.places_nearby(geo, radius, keyword)
            if restaurants is None or len(restaurants) == 0:
                return None
            else:
                restaurant_name = restaurants[0]['name']
                return self.find_place(f"{restaurant_name},{self.city_name}")

    def search_flights(self, departure, destination):
        flight_info = recommend_flights(departure, destination)
        return flight_info

    def places_nearby(self, geo, radius, keyword):
        i = 0
        while i < MAX_TRY:
            try:
                raw_results = self.client.places_nearby(geo, radius, keyword)['results']
                ans = []
                for raw_result in raw_results:
                    result = {k: v for k, v in raw_result.items() if k in interested_key}
                    geo_info = result.pop('geometry')['location']
                    result['gps_coordinates'] = {'latitude': geo_info['lat'], 'longitude': geo_info['lng']}
                    ans.append(result)
                if len(ans) == 0:
                    i += 1
                    time.sleep(1)
                    continue
                return ans
            except BaseException:
                i += 1
                time.sleep(1)

    def directions(self, departure, destination):
        # departure/destination is a dictionary {'latitude':..., 'longitude':...}
        # given these two points, you should call self.client.directions to acquire a route
        #For driving
        parsed_data_driving = self.client.directions(departure, destination, mode="driving")
        #contains total distance and duration
        overall_driving = []
        for leg in parsed_data_driving[0]['legs']:
            # Access the 'distance' object within each leg
            distance = leg['distance']
            # Extract the distance text and value
            distance_text = distance['text']
            overall_driving.append(distance_text)

        for leg in parsed_data_driving[0]['legs']:
            duration = leg['duration']
            duration_text = duration['text']
            overall_driving.append(duration_text)

        #For transit
        time.sleep(1)
        parsed_data_transit = self.client.directions(departure, destination, mode="transit")
        log_info(f"departure:{departure},destination:{destination},mode:transit")
        log_info(parsed_data_transit)

        overall_transit = []
        if len(parsed_data_transit) == 0:
            return "Driving: " + ' '.join(overall_driving)

        for leg in parsed_data_transit[0]['legs']:
            duration = leg['duration']
            duration_text = duration['text']
            overall_transit.append(duration_text)

        for instruction in parsed_data_driving[0]['legs'][0]['steps']:
            html_instruction_text = instruction['html_instructions']
            overall_transit.append(html_instruction_text)

        return "Driving: " + ' '.join(overall_driving) + "\nTransit: " + ' '.join(overall_transit)