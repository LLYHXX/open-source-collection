import logging

import dspy


class ScorerMidwayChat(dspy.Signature):
    judging_criteria = dspy.InputField(desc="the judging criteria")
    query = dspy.InputField(
        desc="the query of the user and the associated chat history"
    )
    response = dspy.InputField(desc="the response by a model")
    judgment = dspy.OutputField(
        desc="judgment of how good the response is to the query with respect to the judging criteria."
    )


class ScorerMidwayChatModule(dspy.Module):
    def __init__(self):
        self.scorer = dspy.ChainOfThought(ScorerMidwayChat)

    def forward(self, judging_criteria, query, response):
        return self.scorer(
            judging_criteria=judging_criteria, query=query, response=response
        ).judgment


class ScorerConcludedChat(dspy.Signature):
    judging_criteria = dspy.InputField(desc="the judging criteria")
    chat_history = dspy.InputField(desc="the chat history of the user with the model")
    judgment = dspy.OutputField(
        desc="judgment of how good the model was throughout the chat with respect to the judging criteria."
    )


class ScorerConcludedChatModule(dspy.Module):
    def __init__(self):
        self.scorer = dspy.ChainOfThought(ScorerConcludedChat, n=1)

    def forward(self, judging_criteria, chat_history):
        return self.scorer(
            judging_criteria=judging_criteria, chat_history=chat_history
        ).judgment


class CheckEvaluationCriteria(dspy.Signature):
    context = dspy.InputField(desc="may contain relevant facts")
    question = dspy.InputField(desc="question asked by the user")
    evaluation_instruction = dspy.InputField(
        desc="Evaluation on the answer based on the context and the question"
    )
    answer = dspy.InputField(desc="answer to the question asked by the user")
    evaluation_judgement = dspy.OutputField(
        desc="describe if the context has the knowledge required to answer the question"
    )


class RAGCheck(dspy.Module):
    def __init__(self, reasoning_strategy="chain_of_thought", **kwargs):
        super().__init__()
        if reasoning_strategy == "chain_of_thought":
            self.evaluation_criteria_module = dspy.ChainOfThought(
                CheckEvaluationCriteria, n=kwargs.get("n", 1)
            )
        else:
            raise ValueError("Invalid reasoning strategy")

    def forward(self, context, question, answer, evaluation_instruction):
        prediction = self.evaluation_criteria_module(
            context=context,
            question=question,
            answer=answer,
            evaluation_instruction=evaluation_instruction,
        )
        logging.info(f"Evaluation Judgement: {prediction.evaluation_judgement}")
        return prediction.evaluation_judgement


class GenerateAnswer(dspy.Signature):
    """Answer questions with short factoid answers."""

    context = dspy.InputField(desc="may contain relevant facts")
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")


class RAG(dspy.Module):
    def __init__(self, num_passages=1):
        super().__init__()

        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate_answer = dspy.ChainOfThought(GenerateAnswer)

    def forward(self, question):
        context = self.retrieve(question).passages
        logging.info(f"Retrieved context: {context}")
        prediction = self.generate_answer(context=context, question=question)
        logging.info(f"Generated answer: {prediction.answer}")
        return dspy.Prediction(context=context, answer=prediction.answer)


class CheckGeneratedAnswer(dspy.Signature):
    """Use the context, question and the answer to check if the answer satisfies the given condition"""

    context = dspy.InputField(desc="may contain relevant facts")
    question = dspy.InputField(desc="question asked by the user")
    answer = dspy.InputField(desc="often between 1 and 5 words")
    condition = dspy.InputField(
        desc="condition to check if the answer satisfies the condition"
    )
    satisfies_condition = dspy.OutputField(
        desc="True if the answer satisfies the condition, False otherwise. Return only the boolean value."
    )


class RAGGenerateCheck(dspy.Module):
    def __init__(self, condition):
        super().__init__()
        self.condition = condition
        self.check_answer = dspy.ChainOfThought(CheckGeneratedAnswer)

    def forward(self, context, question, answer):
        prediction = self.check_answer(
            context=context,
            question=question,
            answer=answer,
            condition=self.condition,
        )
        logging.info(
            f"Checked if answer uses context: {prediction.satisfies_condition}"
        )
        return prediction.satisfies_condition
