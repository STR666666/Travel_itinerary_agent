import json
import numpy as np
from src.tools.travel.serpAPI import distance_calculator
from src.tools.travel.google_map_client import google_map_client
from src.utils.debug import log_info, DEBUG

ONE_DAY_DURATION = 10
SPEED = 30000  # meters/hour
BEST_TIME_SCORE = 16
RETURN_HOME_SCORE = 50
TIME_LEFT_SCORE = 4
THRESHOLD = 50

class RoutePlanner:
    def __init__(self, all_sights, hotel):
        self.hotel = hotel
        self.all_sights = all_sights
        self.gmaps = google_map_client()

    def _calculate_overlap(self, arrive_time, leave_time, recommend_play_time):
        overlaps = []
        for n in range(arrive_time.shape[0]):
            start, end = recommend_play_time[n]
            overlap = sum(start <= (i + int(arrive_time[n]+0.5)) <= end for i in range(int(leave_time[n]+0.5) - int(arrive_time[n]+0.5)))
            overlaps.append(overlap)
        return np.array(overlaps)

    def _calculate_scores(self, available_sights, current_time, current_pos, time_left):
        distances_to_sights = np.array([distance_calculator(current_pos, sight['gps_coordinates']) for sight in available_sights])
        distances_to_hotel = np.array([distance_calculator(sight['gps_coordinates'], self.hotel['gps_coordinates']) for sight in available_sights])
        durations = np.array([sight['recommend_duration'] for sight in available_sights])
        recommend_play_times = np.array([sight['recommend_play_time'] for sight in available_sights])

        time_costs = (distances_to_sights + distances_to_hotel) / SPEED + durations
        return_home_scores = np.where(time_costs < time_left, RETURN_HOME_SCORE, 0)
        
        arrive_times = current_time + distances_to_sights / SPEED
        leave_times = arrive_times + durations
        overlaps = self._calculate_overlap(arrive_times, leave_times, recommend_play_times)
        best_time_scores = overlaps * BEST_TIME_SCORE

        time_left_scores = (time_left - time_costs) * TIME_LEFT_SCORE

        return return_home_scores + best_time_scores + time_left_scores

    def plan_one_day_route(self, available_sights):
        visited = []
        current_pos = self.hotel['gps_coordinates']
        current_time = 9
        time_left = ONE_DAY_DURATION

        while available_sights:
            scores = self._calculate_scores(available_sights, current_time, current_pos, time_left)
            next_sight_index = np.argmax(scores)
            
            if scores[next_sight_index] < THRESHOLD:
                break
            
            next_sight = available_sights.pop(next_sight_index)
            current_pos = next_sight['gps_coordinates']
            current_time += (distance_calculator(self.hotel['gps_coordinates'], current_pos) / SPEED) + next_sight['recommend_duration']
            time_left -= (distance_calculator(self.hotel['gps_coordinates'], current_pos) / SPEED) + next_sight['recommend_duration']
            
            visited.append(next_sight)
            
        return visited, available_sights

    def plan_full_route(self):
        itinerary = []
        remaining_sights = self.all_sights[:]

        while remaining_sights:
            daily_route, remaining_sights = self.plan_one_day_route(remaining_sights)
            
            if not daily_route:
                hotel_location = np.mean([sight['gps_coordinates'].values() for sight in remaining_sights], axis=0).tolist()
                self.hotel = self.gmaps.search_hotel(hotel_location)
                continue
            
            itinerary.append((daily_route, self.hotel))

        log_info(f"Partitioned sights: {json.dumps(itinerary, indent=4)}, Remaining sights: {remaining_sights}")

        return remaining_sights, itinerary