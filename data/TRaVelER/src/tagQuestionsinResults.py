from datetime import datetime
from models import prompt_and_json
import os


class TagQuestions:
    def __init__(self, question_categories, models, event_histories_sizes, prompt_engineering=[]):
        """
        Initialize the class with categories, models, event history sizes, and optional prompt engineering settings.

        Args:
            question_categories (list): List of question categories.
            models (list): List of models to be used.
            event_histories_sizes (list): List of sizes for event histories.
            prompt_engineering (list, optional): List for prompt engineering settings. Defaults to an empty list.
        """
        self.question_categories = question_categories
        self.models = models
        self.event_histories_sizes = event_histories_sizes
        self.prompt_engineering = prompt_engineering
        # Define a list of date formats to be used for parsing dates.
        self.date_formats = ['%Y-%m-%d', '%Y-%m', '%Y', '%d.%m.%Y', '%d/%m/%Y', '%Y/%m/%d', '%m-%d-%Y']

    def _get_first_word(self, text):
        """
        Return the first word of the provided text, or None if the text is empty.

        Args:
            text (str): Input text to extract the first word from.

        Returns:
            str or None: The first word of the text or None if no words are present.
        """
        words = text.split()
        if words:
            return words[0]
        else:
            return None

    def _get_both_last_words(self, text):
        """
        Return the last two words of the provided text, removing any trailing question mark from the last word.

        Args:
            text (str): Input text to extract the last words from.

        Returns:
            tuple or None: A tuple containing the last and second-to-last words, or None if no words are present.
        """
        words = text.split()
        if words:
            last_word = words[-1].replace('?', '')  # Remove any '?' from the last word
            word_before_last = words[-2]
            return last_word, word_before_last
        else:
            return None

    def _check_date_format(self, date_text, date_format):
        """
        Check if the given date_text matches the provided date_format.

        Args:
            date_text (str): The date text to check.
            date_format (str): The format to match against.

        Returns:
            bool: True if the date_text matches the format, False otherwise.
        """
        try:
            datetime.strptime(date_text, date_format)
        except ValueError:
            return False
        return True

    def _find_file(self, results_folder, file_name):
        """
        Search for a file with the specified file_name in the results_folder and its subdirectories.

        Args:
            results_folder (str): The folder to search within.
            file_name (str): The name of the file to find.

        Returns:
            list: A list of full paths to found files.
        """
        found_files = []
        for root, dirs, files in os.walk(results_folder):
            if file_name in files:
                found_files.append(os.path.join(root, file_name))  # Append the full path of found files
        return found_files

    def tag(self):
        """
        Main function to tag questions based on their content and categories.

        This function iterates over each question category, model, and event history size,
        searches for relevant files, processes the questions to generate tags, and saves
        the tagged questions back to the corresponding JSON files.
        """
        for question_category in self.question_categories:  # Iterate through each question category
            for model in self.models:  # Iterate through each model
                for event_sets_size in self.event_histories_sizes:  # Iterate through each event set size
                    # Determine the results folder based on whether prompt engineering is used
                    if not self.prompt_engineering:
                        results_folder = "results/" + str(question_category) + "/" + str(model) + "/"
                    else:
                        results_folder = "results_promptEngineering/" + str(question_category) + "/" + str(model) + "/"

                    # Construct the expected file name
                    file_name = str(event_sets_size) + 'Events.json'
                    # Find the specified file in the results folder
                    files = self._find_file(results_folder, file_name)

                    # Process each found file
                    for file in files:
                        results_file = prompt_and_json.LoadAndSaveJson(file, create_if_not_exist=False)
                        results_file_content = results_file.content  # Load the content of the JSON file

                        for test_case in range(0, len(results_file_content) - 2):  # Iterate through the test cases
                            question = results_file_content[test_case]["Question"]  # Get the question
                            results_file_content[test_case]["Tags"] = []  # Initialize an empty list for tags

                            # Tags according to the question return type based on the first word
                            first_word = self._get_first_word(question)
                            if first_word == "Who":
                                results_file_content[test_case]["Tags"].append("person")
                            elif first_word == "When":
                                results_file_content[test_case]["Tags"].append("date")
                            elif first_word == "Did":
                                results_file_content[test_case]["Tags"].append("bool")
                            elif first_word == "How":
                                results_file_content[test_case]["Tags"].append("int")

                            # Process the last words to determine additional tags
                            last_word, word_before_last = self._get_both_last_words(question)
                            if last_word == "yesterday":
                                results_file_content[test_case]["Tags"].append("yesterday")
                            elif last_word == "today":
                                results_file_content[test_case]["Tags"].append("today")
                            elif last_word == "month":
                                if word_before_last == "this":
                                    results_file_content[test_case]["Tags"].append("this_month")
                                else:
                                    results_file_content[test_case]["Tags"].append("last_month")
                            elif last_word == "year":
                                results_file_content[test_case]["Tags"].append("this_year")
                            else:
                                # Check if the last part of the string contains a date using predefined formats
                                for date_format in self.date_formats:
                                    check = self._check_date_format(last_word, date_format)
                                    if check:
                                        if 'd' in date_format:
                                            results_file_content[test_case]["Tags"].append("day")
                                        elif 'm' in date_format:
                                            results_file_content[test_case]["Tags"].append("month")
                                        elif 'Y' in date_format:
                                            results_file_content[test_case]["Tags"].append("year")

                        # Save the updated content back to the JSON file
                        results_file.save_to_json(results_file_content)


        
