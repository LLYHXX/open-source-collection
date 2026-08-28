"""
Prompt templates for chat initial message generation.

This module centralizes the prompt text used to generate the simulated
customer's first message in chat.
"""

CHAT_INITIAL_MESSAGE_SYSTEM_PROMPT = (
    "You generate realistic first messages for chat conversations where a customer is reaching out to an agent for help. "
    "Output ONLY the message text itself - no labels, no quotes, no explanations. "
    "The message should sound natural and human, matching the character's traits exactly."
)


CHAT_INITIAL_MESSAGE_USER_INSTRUCTIONS = (
    "This customer is INITIATING contact with an agent to get help with their situation. "
    "Generate the FIRST message they would send as their opening statement. "
    "Make it natural, realistic, and true to their character. "
    "They are reaching out and starting this conversation. "
    "Output ONLY the message text - no headings, no labels, no quotes, no meta commentary.\n\n"
    "Realistic Personal Details:\n"
    "- When mentioning personal details (phone/email/address fragments/IDs) of the customer, provide plausible fictional fully-specified values (make them up if needed).\n"
    "- Do NOT use masked placeholders like '98xxxxxxx2', '9XXXXXXXXX', '***', or 'XXX-XXX'.\n"
    "- STRICT: Never use obvious fake patterns (sequential runs, repeated digits, keyboard patterns). Avoid: '9876543210', '1234567890', '1111111111', '0000000000', 'abc123', 'asdf', 'qwerty'.\n"
    "- Keep any invented details consistent and plausible for your persona/location.\n"
    "Output ONLY the message text - nothing else."
)


def build_chat_initial_message_messages(
    *,
    persona_brief: str,
    situation: str,
    guidance: str,
    hint: str,
) -> list[dict[str, str]]:
    """Build the LLM messages payload for chat initial message generation."""
    return [
        {"role": "system", "content": CHAT_INITIAL_MESSAGE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "\n\n".join(
                filter(
                    None,
                    [
                        f"**Character:** {persona_brief}",
                        f"**Situation:** {situation}",
                        "**Character Traits & Writing Style:**",
                        guidance if guidance else "Write naturally and authentically.",
                        f"**Additional Hint:** {hint}" if hint else None,
                        "",
                        CHAT_INITIAL_MESSAGE_USER_INSTRUCTIONS,
                    ],
                )
            ).strip(),
        },
    ]
