import json
import uuid

try:
    from ee.prompts.data_generation_prompts import (
        decompose_prompt,
        evaluate_condition_prompt,
        system_message,
    )
except ImportError:
    decompose_prompt = ""
    evaluate_condition_prompt = ""
    system_message = ""
from ...core.llm.llm import LLM


class ChatMessage:
    def __init__(self, message_id, parent_message_id, role, content, action_taken):
        self.message_id = message_id
        self.parent_message_id = parent_message_id
        self.role = role
        self.content = content
        self.action_taken = action_taken


class ChatHistory:
    def __init__(self, chat_data, llm_client):
        self.messages = self.load_messages(chat_data)
        self.llm_client = llm_client
        self.chat_history = []

    def load_messages(self, chat_data):
        messages = []
        for _role, msgs in chat_data.items():
            for msg in msgs:
                messages.append(
                    ChatMessage(
                        msg["message_id"],
                        msg.get("parent_message_id"),
                        msg["role"],
                        msg["content"],
                        msg.get("action_taken"),
                    )
                )
        return messages

    def count_responses(self, action):
        return sum(
            1
            for msg in self.messages
            if msg.role == "assistant"
            and msg.action_taken
            and action.lower() in msg.action_taken.lower()
        )

    def fraction_responses(self, action):
        total_responses = sum(1 for msg in self.messages if msg.role == "assistant")
        action_responses = self.count_responses(action)
        return action_responses / total_responses if total_responses > 0 else 0

    def percentage_responses(self, action):
        return self.fraction_responses(action) * 100

    def analyze_query(self, query):
        action = None
        query_type = None

        if "like" in query.lower():
            action = "Like"
        elif "dislike" in query.lower():
            action = "Dislike"
        elif "copied" in query.lower():
            action = "Copied"
        elif "edited" in query.lower():
            action = "Edited"

        if "sum" in query.lower():
            query_type = "sum"
        elif "fraction" in query.lower():
            query_type = "fraction"
        elif "percentage" in query.lower():
            query_type = "percentage"

        if not action or not query_type:
            return "Query not understood or action type not supported."

        if query_type == "sum":
            return self.count_responses(action)
        elif query_type == "fraction":
            return self.fraction_responses(action)
        elif query_type == "percentage":
            return self.percentage_responses(action)

    def get_response(self, prompt, parent_message_id):
        message_id = str(uuid.uuid4())
        self.chat_history.append(
            {
                "message_id": message_id,
                "parent_message_id": parent_message_id,
                "role": "user",
                "content": prompt,
                "action_taken": None,
            }
        )

        response = self.llm_client._get_completion_content(
            messages=[
                {"role": "system", "content": system_message},
                *self.chat_history,
            ]
        )
        response_message_id = str(uuid.uuid4())
        self.chat_history.append(
            {
                "message_id": response_message_id,
                "parent_message_id": message_id,
                "role": "assistant",
                "content": response,
                "action_taken": None,
            }
        )
        return response, response_message_id

    def evaluate_condition(self, condition):
        satisfied_count = 0
        for message in self.messages:
            if message.role == "user" and message.action_taken:
                response, _ = self.get_response(
                    evaluate_condition_prompt.format(
                        condition=condition,
                        question=message,
                        answer=(
                            self.get_message_by_id(message.parent_message_id).content
                            if message.parent_message_id
                            else "N/A"
                        ),
                        action=message.action_taken,
                    ),
                    message.message_id,
                )
                if "yes" in response.lower():
                    satisfied_count += 1
        return satisfied_count

    def get_message_by_id(self, message_id):
        for message in self.messages:
            if message.message_id == message_id:
                return message
        return None


class QueryDecomposer:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def get_response(self, prompt):
        response = self.llm_client._get_completion_content(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ]
        )
        return response

    def decompose_query(self, complex_query):
        response = self.get_response(
            decompose_prompt.format(complex_query=complex_query)
        )
        return response.split("\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyzie_chats.py <path_to_chat_history.json>")
        sys.exit(1)

    chat_history_path = sys.argv[1]

    with open(chat_history_path) as f:
        chat_data = json.load(f)

    llm = LLM(model_name="google/gemini-pro")

    chat_history = ChatHistory(chat_data, llm)
    query_decomposer = QueryDecomposer(llm)

    complex_query = "How often the users are not sure about their queries and they take out the anger on us?"

    simple_queries = query_decomposer.decompose_query(complex_query)
    print(f"Decomposed queries for '{complex_query}':\n{simple_queries}\n")

    for simple_query in simple_queries:
        result = chat_history.analyze_query(simple_query)
        print(f"Query: {simple_query}\nResult: {result}\n")
