
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import create_events
import create_questions_gt
import evaluateLLMAnswers
import tagQuestionsinResults
from models.llmRunner import LLMRunner

# Global configuration constants
today_timestamp = 1696018694  # Timestamp for event creation and running
num_events_to_create = 100
patterns = [
    {"Action": "watch", "Object": "film"},
    {"Action": "eat", "Object": "risotto"},
    {"Action": "read", "Object": "book"},
    {"Action": "dance", "Object": "lively salsa"},
    {"Action": "store", "Object": "wine bottle"},
    {"Action": "drink", "Object": "juice"},
    {"Action": "chat with", "Object": "friend"},
]
subjects = ["Mary", "Tom", "Ria"]
locations = ["living room", "kitchen"]
num_explicitolut_questions_to_create = 100
num_relatednow_questions_to_create = 100
tags = ["int", "bool", "person", "date"]  # Tags for evaluation


def run_script():
    """Execute the main functionality based on user selections."""
    try:
        # Gather selected parameters
        question_categories = gather_question_categories()
        length_event_histories = gather_length_event_histories()
        selected_models = gather_selected_models()
        prompt_engineering = is_prompt_engineering_enabled()
        create_events_questions_flag = create_events_questions_var.get()
        run_llms_flag = run_llms_flag_var.get()
        evaluate_flag = evaluate_flag_var.get()

        # Validate selections
        if not validate_selections(create_events_questions_flag, run_llms_flag, evaluate_flag,
                                   length_event_histories, question_categories, selected_models):
            return

        # Execute selected options
        if create_events_questions_flag:
            create_events_and_questions(length_event_histories)

        if run_llms_flag:
            run_llms(length_event_histories, question_categories, selected_models, prompt_engineering)

        if evaluate_flag:
            evaluate_llms(length_event_histories, question_categories, selected_models, prompt_engineering)

        messagebox.showinfo("Success", "Script executed successfully!")
        root.quit()
    except Exception as e:
        messagebox.showerror("Error", str(e))


def gather_question_categories():
    """Collect selected question categories from the GUI."""
    categories = []
    if var_referential.get() == 1:
        categories.append("referential")
    if var_explicit.get() == 1:
        categories.append("explicit")
    return categories


def gather_length_event_histories():
    """Collect selected lengths of event histories from the GUI."""
    return [value for value, var in checkbox_vars.items() if var.get() == 1]


def gather_selected_models():
    """Collect selected models for execution from the GUI."""
    return [model for model, var in model_vars.items() if var.get() == 1]


def is_prompt_engineering_enabled():
    """Check if prompt engineering is enabled based on user selection."""
    return prompt_engineering_var.get() == "Yes"


def validate_selections(create_events_questions_flag, run_llms_flag, evaluate_flag,
                        length_event_histories, question_categories, selected_models):
    """Validate that at least one option is selected and required parameters are filled."""
    if not create_events_questions_flag and not run_llms_flag and not evaluate_flag:
        messagebox.showerror("Error", "You have to select at least one option out of the 'Code to Run' section")
        return False

    if create_events_questions_flag and not length_event_histories:
        messagebox.showerror("Error", "You need to choose the length of the Event Sets to be created")
        return False

    if run_llms_flag and (not length_event_histories or not question_categories or not selected_models):
        messagebox.showerror("Error",
                             "You need to select the length of the Event Sets, question categories, and LLMs to be executed")
        return False

    if evaluate_flag and (not length_event_histories or not question_categories or not selected_models):
        messagebox.showerror("Error",
                             "You need to select the length of the Event Sets, question categories, and LLMs to be evaluated")
        return False

    return True


def create_events_and_questions(length_event_histories):
    """Create events and questions based on the selected length."""
    create_events.CreateEvents(num_events_to_create, patterns, subjects, locations,
                               today_timestamp, save_path="events/").create_events()
    create_questions_gt.generate_questions_and_save(
        length_event_histories, num_explicitolut_questions_to_create,
        num_relatednow_questions_to_create, today_timestamp,
        save_path="dataset", events_path="events/100Events.json"
    )


def run_llms(length_event_histories, question_categories, selected_models, prompt_engineering):
    """Run the selected Large Language Models (LLMs) with the specified parameters."""
    if prompt_engineering:
        LLMRunner(
            today_timestamp, question_categories, length_event_histories,
            model_names=selected_models,
            prompt_engineering_methods=[date_methods_var.get(), event_methods_var.get(), prompting_methods_var.get()],
            prompt_engineering=True
        ).generate_completions()
    else:
        LLMRunner(
            today_timestamp, question_categories, length_event_histories,
            model_names=selected_models
        ).generate_completions()
    return



def evaluate_llms(length_event_histories, question_categories, selected_models, prompt_engineering):
    """Evaluate the benchmarked LLMs with the specified parameters."""
    tagQuestionsinResults.TagQuestions(
        question_categories, selected_models, length_event_histories,
        prompt_engineering=prompt_engineering
    ).tag()
    if prompt_engineering:
        (evaluateLLMAnswers.EvaluateLLMs(
            question_categories, selected_models, tags, length_event_histories,
            prompt_engineering=prompt_engineering,
            prompt_engineering_methods=[date_methods_var.get(), event_methods_var.get(), prompting_methods_var.get()])
         .evaluate())
    else:
        evaluateLLMAnswers.EvaluateLLMs(question_categories, selected_models, tags, length_event_histories,
                                        prompt_engineering=prompt_engineering).evaluate()


def toggle_prompt_methods():
    """Toggle visibility of the prompt engineering methods based on the radio button state."""
    if prompt_engineering_var.get() == "Yes":
        # Show frame
        prompt_methods_frame.grid(row=9, column=0, sticky='w', columnspan=4)
        prompt_date_methods_frame.grid(row=1, column=0, sticky='w', columnspan=4)
        prompt_event_methods_frame.grid(row=2, column=0, sticky='w', columnspan=4)
        prompt_prompting_methods_frame.grid(row=3, column=0, sticky='w', columnspan=4)
    else:
        # Hide frame
        prompt_methods_frame.grid_forget()
        prompt_date_methods_frame.grid_forget()
        prompt_event_methods_frame.grid_forget()
        prompt_prompting_methods_frame.grid_forget()


def setup_ui():
    """Set up the main UI for the application."""
    global create_events_questions_var
    global run_llms_flag_var
    global evaluate_flag_var
    root.title("Parameter and Code to Run Selection")

    # Create a frame for parameter selection
    param_frame = tk.Frame(root)
    param_frame.grid(row=0, column=0, padx=0, pady=20)

    # Parameter Selection label
    tk.Label(param_frame, text="Parameter Selection", font=("Helvetica", 16, "bold")).grid(row=0, column=0,
                                                                                           pady=(0, 20))

    setup_length_event_sets(param_frame)
    setup_question_categories(param_frame)
    setup_large_language_models(param_frame)
    setup_prompt_engineering(param_frame)

    # Create a frame for code to run section
    code_frame = tk.Frame(root)
    code_frame.grid(row=1, column=0, padx=0, pady=0, sticky='w')  # Added sticky='w'

    # Adding Code to Run label
    tk.Label(code_frame, text="Code to Run", font=("Helvetica", 16, "bold")).grid(row=0, column=0, pady=(0, 10),
                                                                                  sticky='w')

    # Create checkboxes for actions
    create_events_questions_var = tk.BooleanVar()
    tk.Checkbutton(code_frame, text="Create new Events and Questions based on them",
                   variable=create_events_questions_var).grid(row=1, column=0, sticky='w', columnspan=4)

    run_llms_flag_var = tk.BooleanVar()
    tk.Checkbutton(code_frame, text="Benchmark LLMs", variable=run_llms_flag_var).grid(row=2, column=0, sticky='w',
                                                                                       columnspan=4)

    evaluate_flag_var = tk.BooleanVar()
    tk.Checkbutton(code_frame, text="Evaluate the benchmarked LLMs", variable=evaluate_flag_var).grid(row=3, column=0,
                                                                                                      sticky='w',
                                                                                                      columnspan=4)

    # Run button
    tk.Button(root, text="Run Script", command=run_script).grid(row=2, column=0, pady=20)

    # Initialize UI to hide the prompt engineering methods
    toggle_prompt_methods()  # Call to set initial visibility


def setup_length_event_sets(parent):
    """Setup UI elements for selecting length of event sets."""
    tk.Label(parent, text="Length Event Sets").grid(row=1, column=0, sticky='w')
    length_frame = tk.Frame(parent)
    length_frame.grid(row=1, column=1, columnspan=3, sticky='w', padx=(0, 0))

    values = [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    global checkbox_vars  # Declare as global to access in other functions
    checkbox_vars = {}
    for idx, value in enumerate(values):
        var = tk.IntVar()
        checkbox_vars[value] = var
        tk.Checkbutton(length_frame, text=str(value), variable=var).grid(row=1, column=idx, padx=0, sticky='w')


def setup_question_categories(parent):
    """Setup UI elements for selecting question categories."""
    tk.Label(parent, text="Question Categories").grid(row=3, column=0, sticky='w')
    global var_referential, var_explicit  # Declare as global to access in other functions
    var_referential = tk.IntVar()
    var_explicit = tk.IntVar()
    tk.Checkbutton(parent, text="Referential", variable=var_referential).grid(row=3, column=1, sticky='w')
    tk.Checkbutton(parent, text="Explicit", variable=var_explicit).grid(row=3, column=2, sticky='w')


def setup_large_language_models(parent):
    """Setup UI elements for selecting large language models (LLMs)."""
    tk.Label(parent, text="Large Language Models").grid(row=5, column=0, sticky='w')
    models = [
        "gpt-4-0125-preview",
        "Meta-Llama-3-8B-Instruct",
        "Meta-Llama-3-70B-Instruct",
        "gemma-7b-it"
    ]
    global model_vars  # Declare as global to access in other functions
    model_vars = {}
    for idx, model in enumerate(models):
        var = tk.IntVar()
        model_vars[model] = var
        tk.Checkbutton(parent, text=model, variable=var).grid(row=5, column=idx + 1, sticky='w')


def setup_prompt_engineering(parent):
    """Setup UI elements for prompt engineering selection."""
    tk.Label(parent, text="Use Prompt Engineering").grid(row=7, column=0, sticky='w')
    global prompt_engineering_var  # Declare as global to access in other functions
    prompt_engineering_var = tk.StringVar(value="No")  # Default value is "No"
    length_frame = tk.Frame(parent)
    length_frame.grid(row=7, column=1, columnspan=3, sticky='w', padx=(0, 0))
    tk.Radiobutton(length_frame, text="Yes", variable=prompt_engineering_var, value="Yes",
                   command=toggle_prompt_methods).grid(row=7, column=0, sticky='w')
    tk.Radiobutton(length_frame, text="No", variable=prompt_engineering_var, value="No",
                   command=toggle_prompt_methods).grid(row=7, column=1, sticky='w')

    # Frame for Prompt Engineering Methods
    global prompt_methods_frame  # Declare as global to access in other functions
    global prompt_date_methods_frame
    global prompt_event_methods_frame
    global prompt_prompting_methods_frame
    prompt_methods_frame = tk.Frame(parent)
    prompt_date_methods_frame = tk.Frame(prompt_methods_frame)
    prompt_event_methods_frame = tk.Frame(prompt_methods_frame)
    prompt_prompting_methods_frame = tk.Frame(prompt_methods_frame)
    date_methods = ["Date-Extended", "Date-Only"]
    event_methods = ["Language", "Json"]
    prompting_methods = ["Zero-Shot", "CoT_Review", "CoT_Step-by-Step"]

    global date_methods_var
    global event_methods_var
    global prompting_methods_var
    date_methods_var = tk.StringVar(value=date_methods[0])
    event_methods_var = tk.StringVar(value=event_methods[0])
    prompting_methods_var = tk.StringVar(value=prompting_methods[0])

    for idx, method_name in enumerate(date_methods):
        (tk.Radiobutton(prompt_date_methods_frame, text=method_name, variable=date_methods_var, value=method_name)
         .grid(row=0, column=idx, sticky='w'))
    for idx, method_name in enumerate(event_methods):
        (tk.Radiobutton(prompt_event_methods_frame, text=method_name, variable=event_methods_var, value=method_name)
         .grid(row=0,column=idx, sticky='w'))
    for idx, method_name in enumerate(prompting_methods):
        (tk.Radiobutton(prompt_prompting_methods_frame, text=method_name, variable=prompting_methods_var, value=method_name)
         .grid(row=0, column=idx, sticky='w'))


# Main execution
root = tk.Tk()
setup_ui()
root.mainloop()