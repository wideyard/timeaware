import datetime
from dateutil.relativedelta import relativedelta
import calendar
from models import prompt_and_json
import pyinflect
import spacy

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")


class DateHelper:
    @staticmethod
    def get_date_in_format(timestamp, date_format):
        """
        Converts a timestamp to a specific date format.

        Args:
            timestamp (int): The timestamp to format.
            date_format (str): The desired date format.

        Returns:
            str: Formatted date string.
        """
        return datetime.datetime.fromtimestamp(timestamp).strftime(date_format)


class ExpressionCategories:
    @staticmethod
    def get_explicit_expressions():
        """
        Provides explicit expressions for date-related questions.

        Returns:
            dict: A dictionary of expressions with their associated date formats and functions.
        """
        return {
            'on': {'date_formats': ['%Y-%m-%d'], 'functions': [DateHelper.get_date_in_format]},
            'in': {'date_formats': ['%Y-%m', '%Y'],
                   'functions': [DateHelper.get_date_in_format]}
        }

    @staticmethod
    def get_related_to_now_expressions(reference_timestamp):
        """
        Generates expressions related to the current date (yesterday, ...).

        Args:
            reference_timestamp (int): The reference timestamp for generating related expressions.

        Returns:
            dict: A dictionary of expressions with their date formats and calculated dates.
        """
        custom_timestamp = datetime.datetime.utcfromtimestamp(reference_timestamp)
        return {
            'today': ['%Y-%m-%d', custom_timestamp.strftime('%Y-%m-%d')],
            'yesterday': ['%Y-%m-%d', (custom_timestamp - datetime.timedelta(1)).strftime('%Y-%m-%d')],
            'this year': ['%Y', custom_timestamp.strftime('%Y')],
            'last month': ['%Y-%m', (custom_timestamp - relativedelta(months=1)).strftime('%Y-%m')],
            'this month': ['%Y-%m', custom_timestamp.strftime('%Y-%m')]
        }


class QuestionTemplates:
    """
    A class for generating question templates based on event details.

    Attributes:
        subject (str): The subject of the question.
        action (str): The action in the question.
        item (str): The item involved in the action.
        location (str): The location of the event.
    """
    def __init__(self, subject, action, item, location):
        self.subject = str(subject)
        self.item = str(item)
        self.action = str(action)
        self.location = str(location)

    def _get_past_tense(self, sentence):
        """
        Converts the verb in the sentence to its past tense form.

        Args:
            sentence (str): The input sentence.

        Returns:
            str: The sentence with the verb in past tense.
        """
        doc = nlp(sentence)
        verb_token = next((token for token in doc if token.pos_ == "VERB"), None)
        if verb_token:
            past_tense = pyinflect.getInflection(verb_token.text, tag='VBD')[0] if pyinflect.getInflection(
                verb_token.text, tag='VBD') else "UNKNOWN_PAST_TENSE"
            past_tense_sentence = sentence.replace(verb_token.text, past_tense, 1)
        else:
            past_tense_sentence = sentence
        return past_tense_sentence

    def _get_who(self, ref_date):
        return self._get_past_tense(f"Who {self.action}{self.item}{self.location} {str(ref_date)}?")

    def _get_did(self, ref_date):
        return f"Did {self.subject}{self.action}{self.item}{self.location} {str(ref_date)}?"

    def _get_howoften(self, ref_date):
        return f"How often did {self.subject}{self.action}{self.item}{self.location} {str(ref_date)}?"

    def _get_whenwasthelasttime(self):
        return self._get_past_tense(f"When was the last time {self.subject}{self.action}{self.item}{self.location}?")


class CreateQuestionsAndGT:
    """
    A class to create questions and ground truth answers from event data.

    Attributes:
        events_for_gt (list): The list of events for generating questions.
        max_number_of_explicit_questions (int): Maximum number of explicitolute questions.
        max_number_of_now_questions (int): Maximum number of now questions.
        reference_timestamp (int): Reference timestamp for generating time-related questions.
    """
    def __init__(self, events_for_gt, max_number_of_explicit_questions, max_number_of_now_questions, reference_timestamp):
        self.events_for_gt = events_for_gt
        self.q_gt_format = ["text", "gt_answers"]
        self.questions_with_gt_now = []
        self.questions_with_gt_explicit = []
        self.max_number_of_explicit_questions = max_number_of_explicit_questions
        self.cur_number_of_explicit_questions = 0
        self.max_number_of_now_questions = max_number_of_now_questions
        self.cur_number_of_now_questions = 0
        self.reference_timestamp = reference_timestamp
        self.expressions = ExpressionCategories

    def _preprocess_patterns(self, subject, item, location):
        """
        Prepares the subject, item, and location strings for question templates.

        Args:
            subject (str): The subject string.
            item (str): The item string.
            location (str): The location string.

        Returns:
            tuple: Preprocessed subject, item, and location strings.
        """
        if subject:
            subject += " "
        else:
            subject = "someone "
        if item:
            item = " " + get_article(item) + " " + str(item)
        else:
            item = ""
        if location:
            location = " in the " + str(location)
        else:
            location = ""
        return subject, item, location

    def _questions(self, event):
        """
        Generates questions (temporally explicit, referential to speech time) for a given event.

        Args:
            event (dict): The event dictionary containing action and related information.

        Returns:
            tuple: Lists of generated questions for now and explicitolute cases.
        """
        if (event["Action"] == ""):
            return ""
        subject, object, location = self._preprocess_patterns(event["Subject"],
                                                              event["Object"],
                                                              event["Location"])
        templates = QuestionTemplates(subject, event["Action"], object, location)
        self._questions_explicit(event, templates)
        self._questions_now(event, templates)
        return self.questions_with_gt_now, self.questions_with_gt_explicit

    def _questions_now(self, event, question_templates):
        """
        Generates referential to speech time questions for a given event.

        Args:
            event (dict): The event dictionary.
            question_templates (QuestionTemplates): The question templates instance.
        """
        if (self.cur_number_of_now_questions >= self.max_number_of_now_questions):
            return
        q_gt = dict.fromkeys(self.q_gt_format, None)

        # When was the last time... question. Only once for every action pattern
        q_gt["text"] = question_templates._get_whenwasthelasttime()
        q_gt["gt_answers"] = self._get_gt_when(event)
        self.questions_with_gt_now.append(q_gt.copy())
        self.cur_number_of_now_questions += 1
        if (self.cur_number_of_now_questions >= self.max_number_of_now_questions):
            return

        for expr in ExpressionCategories.get_related_to_now_expressions(self.reference_timestamp):
            date_format = ExpressionCategories.get_related_to_now_expressions(self.reference_timestamp)[expr][0]
            ref_date = ExpressionCategories.get_related_to_now_expressions(self.reference_timestamp)[expr][1]

            # Who... question with the different expressions for the categorie of related to now questions
            subjects = list(set(self._get_gt_who(event, date_format, ref_date).copy()))
            all_subjects_string = ""
            for subject in subjects:
                all_subjects_string += " " + str(subject)
            q_gt["gt_answers"] = all_subjects_string
            q_gt["text"] = question_templates._get_who(expr)
            self.questions_with_gt_now.append(q_gt.copy())
            self.cur_number_of_now_questions += 1
            if (self.cur_number_of_now_questions >= self.max_number_of_now_questions):
                return

            # Did... question with the different expressions for the categorie of related to now questions
            q_gt["text"] = question_templates._get_did(expr)
            q_gt["gt_answers"] = "no"
            for person in self._get_gt_who(event, date_format, ref_date):
                if person == event["Subject"]:
                    q_gt["gt_answers"] = "yes"
            self.questions_with_gt_now.append(q_gt.copy())
            self.cur_number_of_now_questions += 1
            if (self.cur_number_of_now_questions >= self.max_number_of_now_questions):
                return

            # How often... question with the different expressions for the categorie of related to now questions
            count = 0
            for person in self._get_gt_who(event, date_format, ref_date):
                if person == event["Subject"]:
                    count += 1
            q_gt["gt_answers"] = str(count)
            q_gt["text"] = question_templates._get_howoften(expr)
            self.questions_with_gt_now.append(q_gt.copy())
            self.cur_number_of_now_questions += 1
            if (self.cur_number_of_now_questions >= self.max_number_of_now_questions):
                return

    def _questions_explicit(self, event, question_templates):
        """
        Generates temporally explicit questions for a given event.

        Args:
            event (dict): The event dictionary.
            question_templates (QuestionTemplates): The question templates instance.
        """
        for expr in ExpressionCategories.get_explicit_expressions():
            for function in ExpressionCategories.get_explicit_expressions()[expr]['functions']:
                for date_format in ExpressionCategories.get_explicit_expressions()[expr]['date_formats']:
                    for wrong_correct_date in range(0, 2):
                        timestamp = event["Timestamp"]
                        if wrong_correct_date == 0:
                            ref_date = datetime.datetime.fromtimestamp(event["Timestamp"]).strftime(
                                date_format)
                        else:
                            ref_date = datetime.datetime.fromtimestamp(event["Timestamp"]) - relativedelta(
                                years=2)
                            timestamp = datetime.datetime.timestamp(ref_date)
                            ref_date = ref_date.strftime(date_format)
                        ref_date_expr = str(expr) + " " + function(timestamp, date_format)

                        if (self.cur_number_of_explicit_questions >= self.max_number_of_explicit_questions):
                            return
                        q_gt = dict.fromkeys(self.q_gt_format, None)
                        q_gt["text"] = question_templates._get_who(ref_date_expr)
                        subjects = list(set(self._get_gt_who(event, date_format, ref_date).copy()))
                        all_subjects_string = ""
                        for subject in subjects:
                            all_subjects_string += " " + str(subject)
                        q_gt["gt_answers"] = all_subjects_string
                        self.questions_with_gt_explicit.append(q_gt.copy())
                        self.cur_number_of_explicit_questions += 1

                        if (self.cur_number_of_explicit_questions >= self.max_number_of_explicit_questions):
                            return
                        q_gt["text"] = question_templates._get_did(ref_date_expr)
                        if (len(self._get_gt_who(event, date_format, ref_date)) > 0):
                            q_gt["gt_answers"] = "yes"
                        else:
                            q_gt["gt_answers"] = "no"
                        self.questions_with_gt_explicit.append(q_gt.copy())
                        self.cur_number_of_explicit_questions += 1

                        if (self.cur_number_of_explicit_questions >= self.max_number_of_explicit_questions):
                            return
                        # How often... question with the different expressions for the category of explicit questions
                        q_gt["text"] = question_templates._get_howoften(ref_date_expr)
                        count = 0
                        for person in self._get_gt_who(event, date_format, ref_date):
                            if person == event["Subject"]:
                                count += 1
                        q_gt["gt_answers"] = str(count)
                        self.questions_with_gt_explicit.append(q_gt.copy())
                        self.cur_number_of_explicit_questions += 1

    def _get_gt_who(self, cur_event, date_format, ref_date):
        """
        Retrieves the ground truth for who questions based on the current event and reference date.
        """
        who_gt = []
        cur_pattern_without = cur_event.copy()
        del cur_pattern_without["Subject"]
        del cur_pattern_without["Timestamp"]
        for event in self.events_for_gt:
            date = datetime.datetime.fromtimestamp(event["Timestamp"]).strftime(date_format)
            pattern_without = event.copy()
            del pattern_without["Subject"]
            del pattern_without["Timestamp"]
            if (ref_date == date):
                if (pattern_without == cur_pattern_without):
                    who_gt.append(str(event["Subject"]))
        return who_gt

    def _get_gt_when(self, cur_event):
        """
        Retrieves the ground truth for when questions based on the current event.
        """
        when_gt = ""
        ref_date = datetime.datetime.fromtimestamp(cur_event["Timestamp"])
        cur_pattern_without = cur_event.copy()
        del cur_pattern_without["Timestamp"]
        for event in self.events_for_gt:
            date = datetime.datetime.fromtimestamp(event["Timestamp"])
            pattern_without = event.copy()
            del pattern_without["Timestamp"]
            if (pattern_without == cur_pattern_without and date >= ref_date):
                ref_date = date
                when_gt = str(ref_date.strftime('%Y-%m-%d %H:%M'))
        return when_gt

def get_article(word):
    """
    Determines the appropriate article ('a', 'an', 'some', etc.) for a given word.

    Args:
        word (str): The word for which to determine the article.

    Returns:
        str: The article to use with the word.
    """
    article = 'a'
    if word[0] in ['a', 'e', 'i', 'o', 'u']:
        article = 'an'
    if word == "music":
        article = "to"
    elif word == "flowers" or word == "yoga":
        article = "some"
    elif word == "table":
        article = "the"
    return f"{article}"


def generate_questions_and_save(num_events_for_gt,
                                max_number_of_explicit_questions, max_number_of_now_questions,
                                reference_timestamp,
                                save_path="dataset", events_path="events/100Events.json"):
    """
    Generates questions over all events and saves them to JSON files.

    Args:
        num_events_for_gt (list): Number of events used for generating questions.
        max_number_of_explicit_questions (int): Maximum number of temporally explicit questions.
        max_number_of_now_questions (int): Maximum number of referential to speech time questions.
        reference_timestamp (int): Reference timestamp for generating questions.
        save_path (str): Path to save generated question files.
        events_path (str): Path to the JSON file containing events.
    """
    all_events = prompt_and_json.LoadAndSaveJson(events_path).content

    for gt_events in num_events_for_gt:
        events_limited = all_events[:gt_events]
        create_questions = CreateQuestionsAndGT(events_limited, max_number_of_explicit_questions,
                                                max_number_of_now_questions,
                                                reference_timestamp)

        for event in all_events:
            create_questions._questions(event)

        prompt_and_json.LoadAndSaveJson(f'{save_path}/referential/{gt_events}Events.json').save_to_json(
            create_questions.questions_with_gt_now)
        prompt_and_json.LoadAndSaveJson(f'{save_path}/explicit/{gt_events}Events.json').save_to_json(
            create_questions.questions_with_gt_explicit)
