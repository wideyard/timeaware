import json
from datetime import datetime
import os
import pyinflect
import spacy
from create_questions_gt import get_article

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")

class LoadAndSaveJson:
    """
    A class for loading from and saving to JSON files.
    """
    def __init__(self, file, create_if_not_exist=True):
        """
        Initializes the LoadAndSaveJson class.

        Args:
            file (str): The path to the JSON file.
            create_if_not_exist (bool): Whether to create the file if it doesn't exist (default is True).
        """
        if create_if_not_exist and not os.path.isfile(file):
            directory = os.path.dirname(file)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(file, "w") as f:
                print(str(file) + " is created")
        self.path = file
        self.content = self._load_from_json(self.path)

    @staticmethod
    def _load_from_json(file_name: str) -> dict:
        """
        Loads JSON data from a file.

        Args:
            file_name (str): The name of the file to load.

        Returns:
            dict: The loaded JSON data as a dictionary.
        """
        json_data = {}
        if os.stat(file_name).st_size != 0:
            with open(file_name, 'r') as file_object:
                json_data = json.load(file_object)
        return json_data
    
    def save_to_json(self, content_to_save):
        """
        Saves content to the JSON file.

        Args:
            content_to_save (any): The content to save in JSON format.
        """
        with open(self.path, "w") as jfile:
            json.dump(content_to_save, jfile, indent=4)


class PromptPreparation:
    """
    A class for preparing prompts based on events and questions.
    """
    def __init__(self, today_timestamp, all_action_patterns, num_action_patterns_to_use, prompt_Engineering=[]):
        """
        Initializes the PromptPreparation class.

        Args:
            today_timestamp (int): The current timestamp.
            all_action_patterns (list): A list of all events.
            num_action_patterns_to_use (int): Number of events to use.
            prompt_Engineering (list): Methods for prompt engineering (default is empty).
        """
        self.today_timestamp = today_timestamp
        self.events = all_action_patterns
        for i in range(len(all_action_patterns), num_action_patterns_to_use, -1):
            del self.events[-1]
        self.prompt_Engineering = prompt_Engineering
        if "Language" in self.prompt_Engineering:
            self.dateformat = "%B %d, %Y at %H:%M"  # Natural Language Format
        else:
            self.dateformat = "%Y-%m-%d %H:%M"  # ISO Format
        self._prepare_action_patterns()

    def _remove_tokens(self, content) -> str:
        """
        Removes specific characters from the content to save tokens.

        Args:
            content (str): The content from which to remove tokens.

        Returns:
            str: The cleaned content without specific characters.
        """
        removed_tokens = str(content)
        removed_tokens = removed_tokens.replace("'", "")
        removed_tokens = removed_tokens.replace("[", "")
        removed_tokens = removed_tokens.replace("]", "")
        return removed_tokens
    
    def _answer_restriction(self, question) -> str:
        """
        Defines based on the question, how the LLM should answer.

        Args:
            question (str): The input question.

        Returns:
            str: The restriction for answering the question.
        """
        first_word = question.split()[0]
        if "CoT_Review" in self.prompt_Engineering:
            restriction = ("Review each event out of the event sets sequentially. "
                            "If the action, object, location, subject, and date of an event match the information in the question, respond with 'yes'. "
                            "If this is not the case for all events, answer with 'no'.")
        elif "CoT_Step-by-Step" in self.prompt_Engineering:
            restriction = ("Let's think step by step: Review each event out of the event sets sequentially. "
                "If the action, object, location, subject, and date of an event match the information in the question, respond with 'yes'. "
                "If this is not the case for all events, answer with 'no'.")
        else:
            restriction = "Answer with yes or no."
        if first_word == "Who":
            if "CoT_Review" in self.prompt_Engineering:
                restriction = ("Review each event out of the event sets sequentially. "
                               "If the action, object, location and date of an event match the information in the question, record the subject of that event. "
                               "At the end return the subjects of all matched events.")
            elif "CoT_Step-by-Step" in self.prompt_Engineering:
                restriction = ("Let's think step by step: Review each event out of the event sets sequentially. "
                               "If the action, object, location and date of an event match the information in the question, record the subject of that event. "
                               "At the end return the subjects of all matched events.")
            else:
                restriction = "Answer with the subject names or nobody."
        elif first_word == "How":
            if "CoT_Review" in self.prompt_Engineering:
                restriction = ("Review each event out of the event sets sequentially. "
                               "For each event where the action, object, subject, location and date match the information in the question, "
                               "count +1 and return the summed number at the end.")
            elif "CoT_Step-by-Step" in self.prompt_Engineering:
                restriction = ("Let's think step by step: Review each event out of the event sets sequentially. "
                               "For each event where the action, object, subject, location and date match the information in the question, "
                               "count +1 and return the summed number at the end.")
            else:
                restriction = "Answer with a real number."
        elif first_word == "When":
            if "CoT_Review" in self.prompt_Engineering:
                restriction = ("Review each event out of the event sets sequentially. "
                               "Find all events where the action, object, subject and location match the information in the question. "
                               "From the identified events, ascertain the one that occurred most recently, and return its date and time.")
            elif "CoT_Step-by-Step" in self.prompt_Engineering:
                restriction = ("Let's think step by step: Review each event out of the event sets sequentially. "
                               "Find all events where the action, object, subject and location match the information in the question. "
                               "From the identified events, ascertain the one that occurred most recently, and return its date and time.")
            else:
                restriction = "Answer with a date and its time or nothing."
        return restriction
    
    def _prepare_action_patterns(self):
        """
        Prepares the events by replacing timestamps with formatted date strings.
        The method modifies each action in the events list to include a date and, optionally, the weekday
        and calendar week based on the prompt engineering settings.
        """
        for action in self.events:
            ref_date = datetime.fromtimestamp(action["Timestamp"])
            del action["Timestamp"]
            action["Date"] = str(ref_date.strftime(self.dateformat))
            if "Date-Extended" in self.prompt_Engineering:
                action["Weekday"] = ref_date.strftime('%A')
                action["Calendar Week"] = ref_date.isocalendar()[1]

    def _get_past_tense(self, sentence):
        """
        Converts verbs in a sentence to their past tense forms.

        Args:
            sentence (str): The sentence to process.

        Returns:
            str: The sentence with verbs converted to past tense.
        """
        doc = nlp(sentence)
        verb_token = next((token for token in doc if token.pos_ == "VERB"), None)
        if verb_token:
            past_tense = pyinflect.getInflection(verb_token.text, tag='VBD')[0] if pyinflect.getInflection(
                verb_token.text, tag='VBD') else "UNKNOWN_PAST_TENSE"
            past_tense_sentence = sentence.replace(verb_token.text, past_tense, 1)
        else:
            past_tense_sentence = sentence
        #Sometimes dance, practice, store is not converted to danced
        if "dance" in past_tense_sentence and not "danced" in past_tense_sentence:
            past_tense_sentence = past_tense_sentence.replace("dance", "danced")
        elif "practice" in past_tense_sentence and not "practiced" in past_tense_sentence:
            past_tense_sentence = past_tense_sentence.replace("practice", "practiced")
        elif "store" in past_tense_sentence and not "stored" in past_tense_sentence:
            past_tense_sentence = past_tense_sentence.replace("store", "stored")
        return past_tense_sentence

    def get_prompt_components(self, question):
        """
        Generates the components of the final prompt for the LLM based on the question.

        Args:
            question (str): The input question for which to generate prompt components.

        Returns:
            tuple: A tuple containing the action prompt, answer restriction, today's restriction, and the modified question.
        """
        restriction = self._answer_restriction(question)
        if "Language" in self.prompt_Engineering:
            today_restriction = "Today's date is " + str(
                (datetime.fromtimestamp(self.today_timestamp)).strftime("%B %d, %Y, and the time is %H:%M")) + (".")
            action_prompt = "I have a list of events (event sets) that have occurred in the past, including who did what, where and when: "
            for event in self.events:
                article = get_article(event["Object"])
                if "Date-Extended" in self.prompt_Engineering:
                    temp = ("On " + event["Date"] + " which was a " + str(event["Weekday"]) + " in calendar week " + str(event["Calendar Week"])
                                + ", " + event["Subject"] + " " + event["Action"] + " " + article + " " + event["Object"] + " in the " + event["Location"] + ". ")
                else:
                    temp = ("On " + event["Date"] + ", " + event["Subject"] + " " + event["Action"] + " " + article + " " + event[
                        "Object"] + " in the " + event["Location"] + ". ")

                action_prompt += self._get_past_tense(temp)
            date = question.split()[-1].replace("?","")
            question = question.replace(date+"?", "")
            date_formats = ["Y", '%Y-%m', "%Y-%m-%d"]
            parsed_date = date
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date, date_format)
                    if "%d" in date_format:
                        parsed_date = parsed_date.strftime("%B %d, %Y")
                    elif "%m" in date_format:
                        parsed_date = parsed_date.strftime("%B %Y")
                    else:
                        parsed_date = parsed_date.strftime("%Y")
                    break
                except ValueError:
                    pass
            question = "Now, I want to know: " + question + "" + str(parsed_date) + "?"
        else:
            if "Date-Extended" in self.prompt_Engineering:
                today_weekday = datetime.fromtimestamp(self.today_timestamp).strftime('%A')
                today_calendarweek = datetime.fromtimestamp(self.today_timestamp).isocalendar()[1]
                today_restriction = ("Today is the " +
                                     str((datetime.fromtimestamp(self.today_timestamp)).strftime(self.dateformat)) +
                                     ", a " + today_weekday + " in calendar week " + str(today_calendarweek) + ".")
            else:
                today_restriction = ("Today is the " + str((datetime.fromtimestamp(self.today_timestamp)).strftime(self.dateformat)) + ".")
            action_prompt = "I will give you a list, when specific events have taken place (event sets): " + str(self.events) + ". "
        action_prompt = self._remove_tokens(action_prompt)
        return action_prompt, restriction, today_restriction, question


        
