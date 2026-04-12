import random
import datetime
from models import prompt_and_json


class CreateEvents:
    """
    A class to create events based on provided patterns (containing Action, Object), subjects, and locations.
    """
    def __init__(self, num_events, patterns, subjects, locations, end_timestamp, save_path="events/"):
        """
        Initializes the CreateEvents class.

        Args:
            num_events (int): The number of events to create.
            patterns (list): The patterns (Actions with corresponding Objects).
            subjects (list): The subjects involved in the events.
            locations (list): The locations where events take place.
            end_timestamp (int): The timestamp representing the end date for event generation.
            save_path (str): The directory path to save the events JSON file.
        """
        self._num_events = num_events
        self._patterns = patterns
        self._subjects = subjects
        self._locations = locations
        self._safe_path = save_path + str(num_events) + "Events.json"

        # Calculate date boundaries for generating timestamps
        today = datetime.datetime.utcfromtimestamp(end_timestamp).strftime("%d %b %Y")
        today = datetime.datetime.strptime(today, "%d %b %Y").date()

        start_of_today = datetime.datetime(today.year, today.month, today.day, 0, 0, 0).timestamp()
        end_of_today = datetime.datetime(today.year, today.month, today.day, 23, 59, 59).timestamp()

        start_of_yesterday = datetime.datetime(today.year, today.month, today.day - 1, 0, 0, 0).timestamp()
        end_of_yesterday = datetime.datetime(today.year, today.month, today.day - 1, 23, 59, 59).timestamp()

        start_of_month = datetime.datetime(today.year, today.month, 1, 0, 0, 0).timestamp()
        end_of_month = datetime.datetime(today.year, today.month, today.day - 2, 23, 59, 59).timestamp()

        start_of_lastmonth = datetime.datetime(today.year, today.month - 1, 1, 0, 0, 0).timestamp()
        end_of_lastmonth = datetime.datetime(today.year, today.month - 1, 30, 23, 59, 59).timestamp()

        start_of_thisyear = datetime.datetime(today.year, 1, 1, 0, 0, 0).timestamp()
        end_of_thisyear = datetime.datetime(today.year, today.month - 2, 30, 23, 59, 59).timestamp()

        self.keys = ["Action", "Object", "Location", "Subject", "Timestamp"]
        self.dates_to_match = {'today': [start_of_today, end_of_today],
                              'yesterday': [start_of_yesterday, end_of_yesterday],
                              'this year': [start_of_thisyear, end_of_thisyear],
                              'last month': [start_of_lastmonth, end_of_lastmonth],
                              'this month': [start_of_month, end_of_month]}
        self.dates_list = []
        # Collect timestamp boundaries into a flat list
        for key, value in self.dates_to_match.items():
            self.dates_list.extend(value)


    def create_events(self):
        """
        Creates a specified number of events based on actions, objects, subjects, locations, and random timestamps.
        The method constructs events, assigns a random timestamp from the predefined date ranges, and saves them as a JSON file.
        """
        event_dict = dict.fromkeys(self.keys, None)
        events = []
        cur_num_events = 0
        cur_subject_pos = 0
        cur_location_pos = 0

        # Loop until the specified number of events is created
        while (cur_num_events < self._num_events):
            curr_timestamp = 0
            for pattern in self._patterns:
                event_dict["Subject"] = self._subjects[cur_subject_pos]
                cur_subject_pos += 1
                if (cur_subject_pos >= len(self._subjects)):
                    cur_subject_pos = 0

                event_dict["Location"] = self._locations[cur_location_pos]
                cur_location_pos += 1
                if (cur_location_pos >= len(self._locations)):
                    cur_location_pos = 0

                # Constructs action pattern
                event_dict.update(pattern)

                # random timestamp laying in today, yesterday, this year, last month, this month
                event_dict["Timestamp"] = random.randrange(self.dates_list[curr_timestamp],
                                                                     self.dates_list[curr_timestamp + 1])
                curr_timestamp += 2
                if curr_timestamp >= len(self.dates_list):
                    curr_timestamp = 0


                events.append(event_dict.copy())

                cur_num_events += 1
                if (cur_num_events >= self._num_events):
                    break;

            # Save the created events to a JSON file
            prompt_and_json.LoadAndSaveJson(self._safe_path, ).save_to_json(events)

