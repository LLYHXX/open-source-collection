AGENT_PROMPT_OPTIMISER_RUN_STEPS = [
    {
        "name": "Onboard/initializing",
        "description": "Initializing the optimization process and setting up the environment.",
    },
    {
        "name": "Running baseline eval",
        "description": "Evaluating the performance of the initial baseline prompt to establish a benchmark.",
    },
    {
        "name": "Starting trials/starting optimization",
        "description": "Beginning the iterative process of generating and testing new prompt variations.",
    },
    {
        "name": "Finalizing agent prompt",
        "description": "Selecting the best-performing prompt and completing the optimization run.",
    },
]


AGENT_PROMPT_OPTIMISER_RUN_TABLE_CONFIG = [
    {
        "id": "optimisation_name",
        "name": "Optimisation Name",
        "is_visible": True,
    },
    {
        "id": "started_at",
        "name": "Started At",
        "is_visible": True,
    },
    {
        "id": "no_of_trials",
        "name": "No. of Trials",
        "is_visible": True,
    },
    {
        "id": "optimiser_type",
        "name": "Optimisation Type",
        "is_visible": True,
    },
    {
        "id": "status",
        "name": "Status",
        "is_visible": True,
    },
]


TRIAL_TABLE_BASE_COLUMNS = [
    {"id": "trial", "name": "Trial", "is_visible": True},
    # {"id": "score", "name": "Score", "is_visible": True},
    # {"id": "score_percentage_change", "name": "Score % Change", "is_visible": True},
    {"id": "prompt", "name": "Prompt", "is_visible": True},
    # {"id": "is_best", "name": "Is Best", "is_visible": True},
]

TRIAL_TABLE_EVAL_COLUMNS = [
    {"id": "eval_name", "name": "Eval Name", "is_visible": True},
    {"id": "eval_template_description", "name": "Description", "is_visible": False},
    {"id": "score", "name": "Score", "is_visible": True},
    {"id": "score_percentage_change", "name": "Score % Change", "is_visible": True},
]


TRIAL_TABLE_SCENARIOS_COLUMNS = [
    {"id": "input_text", "name": "Input", "is_visible": True},
    {"id": "output_text", "name": "Output", "is_visible": True},
]
