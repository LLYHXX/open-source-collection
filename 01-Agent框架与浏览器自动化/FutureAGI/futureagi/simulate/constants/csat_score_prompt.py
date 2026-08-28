CSAT_SCORE_PROMPT = {
    "name": "csat_score",
    "description": "Evaluates the Customer Satisfaction (CSAT) score for a chat between the customer and the agent.",
    "criteria": "Assess the overall satisfaction expressed by the customer during the interaction. Consider explicit statements (e.g., 'thank you, this was helpful', 'this is frustrating') as well as implicit behavioral cues such as tone, cooperation, politeness, engagement, or dissatisfaction. Assign a single CSAT score from 1 to 10, where 1 indicates very dissatisfied and 10 indicates very satisfied. Only use evidence present in the interaction; do not infer beyond what is clearly communicated.",
    "choices": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    "multi_choice": False,
}
