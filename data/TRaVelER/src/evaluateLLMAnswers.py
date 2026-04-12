import re
import matplotlib.pyplot as plt
from models import prompt_and_json
import datetime


class ExtractRegularExpressions:
    """
    A class to extract specific regular expressions from text, including dates, times, names, yes/no responses, and integers.
    """
    def __init__(self):
        """
        Initializes the class with a list of names to match in the text.
        """
        self.names_to_match = ["tom", "alex", "mary", "ria",
                               "sammy", "theodore roosevelt", "bob", "subject: none", "no one", "mrs. taylor", "anyone",
                               "any of",
                               "none of", "subject is not specified", "robert"]

    def _help_extract_dates_times(self, text):
        """
        Helper function to extract dates and times from the given text using regular expressions.

        Args:
            text (str): The input text from which to extract dates and times.

        Returns:
            list: A list of matched date and time strings.
        """
        text = text.replace(",", "")
        text = text.replace("at ", "")
        text = text.lower()
        datetime_regex = r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december) \d{1,2} \d{4} \d{1,2}:\d{2}(?::\d{2})?\b'
        datetime_matches = re.findall(datetime_regex, text)
        if not datetime_matches:
            datetime_regex = r'\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}\b'
            datetime_matches = re.findall(datetime_regex, text)
        return datetime_matches

    def extract_dates_times(self, text):
        """
        Extracts and formats dates and times from the provided text.

        Args:
            text (str): The input text from which to extract dates and times.

        Returns:
            list: A list of formatted date and time strings.
        """
        datetime_matches = self._help_extract_dates_times(text)
        formatted_dates = []
        dt = None
        if (len(datetime_matches) > 20):  #unnecessary listing of events
            datetime_matches = []
        elif (len(datetime_matches) > 1):  # take the date from the last sentence - the last date
            sentences = text.split('\n')
            for sentence in sentences:
                if "today" in sentence:
                    datetime_matches.remove(self._help_extract_dates_times(sentence)[0])
            if (len(datetime_matches) > 1):
                datetime_matches = [datetime_matches[-1]]
        if "not mentioned" in text or "didn't find any event that matches these criteria" in text or "no matching event" in text or "no event that matches the question" in text:
            datetime_matches = []
        for match in datetime_matches:
            try:
                dt = datetime.datetime.strptime(match, "%B %d %Y %H:%M")
            except ValueError:
                try:
                    dt = datetime.datetime.strptime(match, "%Y-%m-%d %H:%M")
                except ValueError:
                    print(f"Could not parse date from response: {text}")
            formatted_dates.append(dt.strftime("%Y-%m-%d %H:%M"))
        return formatted_dates

    def extract_llamainformation(self, input_string):
        """
        Extracts specific information about names based on patterns in the input string.
        Specifically written for the response from the LLama Model.

        Args:
            input_string (str): The input string from which to extract names.

        Returns:
            str: A comma-separated string of names found in the input string, or the last line if no specific names are found.
        """
        lines = input_string.split('\n')
        names = []
        for line in lines:
            if "* mary" in line:
                names.append("* mary")
            elif "* ria" in line:
                names.append("* ria")
            elif "* tom" in line:
                names.append("* tom")
        if names:
            return ', '.join(names)
        for line in lines:
            if "subjects of the matched events are" in line \
                    or "subjects of all matched events are" in line \
                    or "subject of the matched event is" in line \
                    or "subject of this event is" in line:
                return line.split(":")[-1].strip()
        if lines and lines[-1].strip() and re.match(r'^\d+\.', lines[-1].strip()):
            return ""
        else:
            return lines[-1]

    def extract_names(self, text, model):
        """
        Extracts names from the given text based on certain patterns and the specified LLM.

        Args:
            text (str): The input text from which to extract names.
            model (str): The model type, which may affect the extraction logic.

        Returns:
            list: A list of unique names extracted from the text.
        """
        sentences_to_match = text.lower().replace('"', '')
        if "Llama" in model:
            sentences_to_match = self.extract_llamainformation(sentences_to_match)
        names_to_match_with_is = [r'is ' + name for name in self.names_to_match]
        name_pattern_is = r'\b(?:' + '|'.join(names_to_match_with_is) + r')\b'
        matched_names = re.findall(name_pattern_is, sentences_to_match, flags=re.IGNORECASE)
        matched_names = [name.replace("is ", "") for name in matched_names]
        if (len(matched_names) == 0):
            name_pattern = r'\b(?:' + '|'.join(self.names_to_match) + r')\b'
            matched_names = re.findall(name_pattern, sentences_to_match, flags=re.IGNORECASE)
        matched_names = [name.lower() for name in matched_names]
        matched_names = list(dict.fromkeys(matched_names))
        if len(matched_names) == 0 and text != "":
            matched_names = ["no_name"]
        elif ("subject: none" in matched_names or "no one" in matched_names
              or "anyone" in matched_names or "any of" in matched_names
              or "none of" in matched_names or "not specified" in matched_names):
            matched_names = [""]
        text_to_match = text.lower().replace('"', '')
        if ("no events" in text_to_match
                or "no match for the" in text_to_match
                or "dates don't match" in text_to_match
                or "date does not match" in text_to_match
                or "question doesn't match" in text_to_match
                or "date doesn't match" in text_to_match
                or "no matched events" in text_to_match
                or "no event" in text_to_match
                or "no subjects who" in text_to_match
                or "not find any event" in text_to_match
                or "no one" in text_to_match):
            matched_names = []
        return matched_names

    def extract_yesno(self, text):
        """
        Extracts 'yes' or 'no' responses from the given text.

        Args:
            text (str): The input text from which to extract yes/no responses.

        Returns:
            list: A list containing the last matched yes/no response or an empty list if none found.
        """
        yes_no = ["yes", "no"]
        name_pattern = r'\b(?:' + '|'.join(yes_no) + r')\b'
        matched_yesno = re.findall(name_pattern, text, flags=re.IGNORECASE)
        matched_yesno = [name.lower() for name in matched_yesno]
        if "i cannot" in text:
            return ["no"]
        if len(matched_yesno) > 0:
            return matched_yesno[-1]
        else:
            return []

    def extract_integer(self, text):
        """
        Extracts integers or their textual representations from the input text.

        Args:
            text (str): The input text from which to extract integers.

        Returns:
            list: A list of extracted integers as strings.
        """
        text = text.lower()
        text = text.replace("[", "")
        text = text.replace("]", "")
        text = text.replace("'", "")
        word_to_number = {
            'i cannot': '0',
            'zero': '0',
            'did not': '0',
            'does not contain': '0',
            'does not include': '0',
            'once': '1',
            'twice': '2'
        }
        word_pattern = '|'.join(re.escape(word) for word in word_to_number.keys())
        integer_regex = r'\b(?:(?<=\s)|(?<=^))[+]?(?:[0-5]|%s)\b' % word_pattern  #Only up to 5 because more then 5 events are not possible
        integers = re.findall(integer_regex, text)
        integer_strings = [integer.replace(',', '') for integer in integers]
        for integer in integers:
            if integer in word_to_number:
                integer_strings = [str(word_to_number[integer])]
        #Only take the last element because first elements are mostly unuseful numbers from enumerations
        if (len(integer_strings) > 1):
            integer_strings = [str(integer_strings[-1])]
        return integer_strings

    def get_first_word(self, text):
        words = text.split()
        if words:
            return words[0]
        else:
            return None

    def string_to_list(self, text):
        cleaned_string = text.replace('[', '').replace(']', '').replace('"', '').replace("'", '')
        values_list = cleaned_string.split(',')
        return values_list


class EvaluateLLMs:
    def __init__(self, question_categories, models, tags, event_histories_sizes, prompt_engineering, prompt_engineering_methods=[]):
        self.question_categories = question_categories
        self.models = models
        self.tags = tags
        self.event_histories_sizes = event_histories_sizes
        self.prompt_engineering_methods = prompt_engineering_methods
        self.prompt_engineering = prompt_engineering

    def _clean_and_strip_list(self, lst):
        cleaned_list = [item.strip() for item in lst if item.strip() != ""]
        return cleaned_list

    def _calculate_confusion_metrics(self, ground_truth, predicted):
        ground_truth_cleaned = self._clean_and_strip_list(ground_truth)
        predicted_cleaned = self._clean_and_strip_list(predicted)
        # Handle empty lists case
        if not ground_truth_cleaned and not predicted_cleaned:
            return 1
        if not predicted_cleaned:
            return 0
        if not ground_truth_cleaned:
            return 0
        correct_classified = sum(1 for item in predicted_cleaned if
                                 any(re.match(re.escape(item), truth, re.IGNORECASE) for truth in ground_truth_cleaned))
        if correct_classified == len(ground_truth_cleaned):
            return 1
        else:
            return 0

    def _calculate_accuracy(self, tp, count_predictions=100):
        return tp / count_predictions if count_predictions else 0

    def plot_and_save_line_graph(self, x_values, y_values_dict, y_label='', title='', save_path=None):
        plt.figure(figsize=(10, 6))
        plt.rc('font', size=12)  # steuert die Standardtextgröße
        plt.rc('xtick', labelsize=10)  # Schriftgröße der x-Tick-Labels
        plt.rc('ytick', labelsize=10)

        label_mapping = {"Flan-T5-base": "FLAN-T5", "Flan-ul2": "FLAN-UL2", "Llama2-13b-chat-hf": "Llama2-13B-Chat",
                         "Llama2-70b-chat-hf": "Llama2-70B-Chat", "gpt-4-0613": "GPT-4"}
        for label, y_values in y_values_dict.items():
            plt.plot(x_values[:len(y_values)], y_values, label=label_mapping.get(label, label), alpha=0.35, lw=3)

        plt.xlabel("Number of Events")
        plt.ylabel(y_label)
        plt.title(title)
        plt.legend()
        plt.xlim(0, x_values[-1] + 5)  # Set x-axis limits
        plt.ylim(0, 1.1)  # Set y-axis limits
        plt.grid(True)
        if save_path:
            plt.savefig(save_path)
            print(f"Plot saved as {save_path}")
        else:
            plt.show()

    def evaluate(self):
        for question_category in self.question_categories:
            accuracy_dict = {model: [] for model in
                             self.models}  # Dictionary to accumulate accuracy values for each model
            for model in self.models:
                for tag in self.tags:
                    if not self.prompt_engineering:
                        evaluation_file = prompt_and_json.LoadAndSaveJson(
                            f'results/{question_category}/{model}'
                            f'/results.json')
                        tag_evaluation_file = prompt_and_json.LoadAndSaveJson(
                            f'results/{question_category}/{model}'
                            f'/tag_{str(tag)}_results.json')
                    else:
                        result_string = "_".join(self.prompt_engineering_methods)
                        evaluation_file = prompt_and_json.LoadAndSaveJson(
                            f'results_promptEngineering/{question_category}/{model}'
                            f'/{result_string}'
                            f'/results.json')
                        tag_evaluation_file = prompt_and_json.LoadAndSaveJson(
                            f'results_promptEngineering/{question_category}/{model}'
                            f'/{result_string}'
                            f'/tag_{str(tag)}_results.json')

                    text_to_save = ["", "Event sets size:", self.event_histories_sizes]
                    tag_text_to_save = ["", "Event sets size:", self.event_histories_sizes]
                    accuracy_temp = []
                    tag_accuracy_temp = []

                    for event_sets_size in self.event_histories_sizes:
                        if not self.prompt_engineering:
                            results_file = prompt_and_json.LoadAndSaveJson(
                                f'results/{question_category}/{model}'
                                f'/{str(event_sets_size)}Events.json', create_if_not_exist=False).content
                        else:
                            result_string = "_".join(self.prompt_engineering_methods)
                            results_file = prompt_and_json.LoadAndSaveJson(
                                f'results_promptEngineering/{question_category}/{model}'
                                f'/{result_string}'
                                f'/{str(event_sets_size)}Events.json', create_if_not_exist=False).content

                        expr_extraction = ExtractRegularExpressions()
                        correct_classified = 0
                        tag_correct_classified = 0
                        tag_num_questions = 0
                        for test_case in range(0, len(results_file) - 2):
                            gt = expr_extraction.string_to_list(results_file[test_case]["GT"])
                            question = results_file[test_case]["Question"]
                            response = results_file[test_case]["Response"]
                            response = response.lower()
                            if "gemma" in model:
                                split_sentence = response.split('<start_of_turn>model', 1)
                                response = split_sentence[-1].strip()
                            if ("answer" in response and not "answer would be" in response) or "result" in response:
                                split_sentence = response.split('answer', 1)
                                predicted = split_sentence[-1].strip()
                            if expr_extraction.get_first_word(question) == "When":
                                predicted = expr_extraction.extract_dates_times(response)
                            elif expr_extraction.get_first_word(question) == "Who":
                                predicted = expr_extraction.extract_names(response, model)
                                if "no_name" in predicted:
                                    predicted.remove("no_name")
                                gt = results_file[test_case]["GT"].split(' ')
                            elif expr_extraction.get_first_word(question) == "Did":
                                predicted = expr_extraction.extract_yesno(response)
                            elif expr_extraction.get_first_word(question) == "How":
                                predicted = expr_extraction.extract_integer(response)

                            correct_classified_temp = self._calculate_confusion_metrics(gt, predicted)
                            correct_classified += correct_classified_temp

                            if tag in results_file[test_case]["Tags"]:
                                tag_num_questions += 1
                                tag_correct_classified += correct_classified_temp

                        accuracy_temp.append(self._calculate_accuracy(correct_classified))
                        tag_accuracy_temp.append(
                            self._calculate_accuracy(tag_correct_classified, count_predictions=tag_num_questions))

                    text_to_save.append("Accuracy:")
                    text_to_save.append(accuracy_temp)
                    overall_acc = 0
                    for acc in accuracy_temp:
                        overall_acc += acc
                    text_to_save.append("Overall:")
                    text_to_save.append(overall_acc / len(accuracy_temp))
                    evaluation_file.save_to_json(text_to_save)
                    accuracy_dict[model] = accuracy_temp

                    tag_text_to_save.append("Accuracy:")
                    tag_text_to_save.append(tag_accuracy_temp)
                    overall_acc = 0
                    for acc in tag_accuracy_temp:
                        overall_acc += acc
                    tag_text_to_save.append("Overall:")
                    tag_text_to_save.append(overall_acc / len(tag_accuracy_temp))
                    tag_evaluation_file.save_to_json(tag_text_to_save)

            # Plot Precision and Recall for the different questions categories and save them in the folder
            if not self.prompt_engineering:
                plot_file_path = f'results/{question_category}/accuracy.png'
                if question_category == "referential":
                    question_category = "referential to now"
                self.plot_and_save_line_graph(self.event_histories_sizes, accuracy_dict, y_label="Accuracy",
                                              title="Accuracy for the category of " + str(
                                                  question_category) + " questions",
                                              save_path=plot_file_path)
