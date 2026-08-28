import json

with open("accounts/demo_dataset/table_data.json") as f:
    dataset_data = json.load(f)

with open("accounts/demo_dataset/run_prompt_config.json") as f:
    run_prompt_config = json.load(f)

prompt_config = [
    {
        "name": "Generate Answer-1",
        "model": ["o1-mini"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Craft the most effective, clear, and concise answer (fewer than 50 words).\nQuestion: {{cf635e5b-92af-460d-a62b-8b22c64287d9}}\nDetails: {{4a502202-ad6e-4cea-a295-426cf977dfb4}}",
                    }
                ],
            }
        ],
        "configuration": {
            "top_p": 1,
            "max_tokens": 8190,
            "temperature": 0.5,
            "response_format": None,
            "presence_penalty": 1,
            "frequency_penalty": 1,
        },
    }
]

with open("accounts/demo_dataset/experiment.json") as f:
    experiment_data = json.load(f)

with open("accounts/demo_dataset/img_dataset_data.json") as f:
    image_dataset_data = json.load(f)
