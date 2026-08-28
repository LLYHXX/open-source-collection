"""
Persona-to-guidance lookup tables used to build simulation prompts.

These dictionaries map normalized persona attribute values (typically
lower-cased) to short guidance snippets that are embedded into the simulator's
persona prompt for voice and chat.
"""

# Voice guides — requires Enterprise Edition.
# Empty fallback so non-voice code that imports this module doesn't crash.
# Voice simulation code paths will fail via other ee.voice guards before
# these empty dicts are ever used.
try:
    from ee.voice.constants.persona_prompt_guides import (  # noqa: F401
        VOICE_COMMUNICATION_STYLE_GUIDES,
        VOICE_PERSONALITY_GUIDES,
    )
except ImportError:
    VOICE_PERSONALITY_GUIDES: dict[str, str] = {}
    VOICE_COMMUNICATION_STYLE_GUIDES: dict[str, str] = {}

CHAT_PERSONALITY_GUIDES: dict[str, str] = {
    "friendly and cooperative": "Warm, approachable, and collaborative. Show genuine interest; keep it natural, not overly polite.",
    "professional and formal": "Professional and formal, but not robotic. Stay focused; avoid repeated 'thank you' or overly scripted phrasing.",
    "cautious and skeptical": "Question and verify before agreeing. Ask clarifying questions; express concerns when things don't add up.",
    "impatient and direct": "Short, to-the-point messages. Minimal small talk; push to resolve quickly.",
    "detail-oriented": "Care about specifics. Ask for details and confirm facts; don't gloss over important info.",
    "easy-going": "Relaxed and flexible. Don't overthink; keep it laid-back.",
    "anxious": "Worried and uncertain. Ask for reassurance; request simple explanations.",
    "confident": "Self-assured and decisive. State what you think clearly; don't hedge constantly.",
    "analytical": "Logical and systematic. Break down options; decide based on reasoning.",
    "emotional": "Express feelings clearly. React naturally; use emotive language when it fits.",
    "reserved": "Measured and private. Keep messages brief; don't overshare.",
    "talkative": "Engaged and chatty. Write longer, more detailed messages, but still like real texting (not essays).",
}

CHAT_COMMUNICATION_STYLE_GUIDES: dict[str, str] = {
    "direct and concise": "Brief and clear. Get to the point; don't ramble.",
    "detailed and elaborate": "Explain with context and examples, but keep it chat-natural (no long paragraphs).",
    "casual and friendly": "Relaxed, conversational language. Warm but not overly polite.",
    "formal and polite": "Courteous and formal. Keep it professional without sounding scripted.",
    "technical": "Use precise, technical terms when relevant. Prioritize accuracy.",
    "simple and clear": "Plain language. Avoid jargon; break things down simply.",
    "questioning": "Ask clarifying questions often. Verify understanding.",
    "assertive": "State needs clearly and directly. Don't be hesitant.",
    "passive": "Accommodating and indirect. Avoid pushing too hard.",
    "collaborative": "Work together; build on ideas and suggestions.",
}

CHAT_TONE_GUIDES: dict[str, str] = {
    "formal": "Use a formal, professional tone. Write clearly without sounding scripted or overly polite.",
    "neutral": "Balanced and clear. Neither stiff nor overly casual.",
    "casual": "Relaxed, informal chat. Contractions and casual phrasing are fine.",
}

CHAT_VERBOSITY_GUIDES: dict[str, str] = {
    "brief": "Very short. Often one sentence or fragment. No paragraphs.",
    "balanced": "Short. Usually 1-2 sentences; only necessary detail.",
    "detailed": "More detail, still chat-natural. Usually 2-3 sentences; avoid long paragraphs.",
}

CHAT_REGIONAL_MIX_GUIDES: dict[str, str] = {
    "none": "Single-language only. No regional mixing.",
    "light": "Light mixing (1-2 times per conversation) when it feels natural (e.g., 'ji', 'haan', 'acha', 'theek hai').",
    "moderate": "Moderate mixing (2-4 times per conversation). Code-switch naturally.",
    "heavy": "Heavy mixing (4+ times per conversation). Frequent code-switching.",
}

CHAT_SLANG_LEVEL_GUIDES: dict[str, str] = {
    "none": "No slang. Standard language only.",
    "light": "Light slang (1-2 times per conversation). Keep it widely understood.",
    "moderate": "Moderate slang (2-4 times per conversation). Include common informal terms/abbreviations.",
    "heavy": "Heavy slang (4+ times per conversation). Casual internet language and age-appropriate slang.",
}

CHAT_TYPO_LEVEL_GUIDES: dict[str, str] = {
    "none": "Perfect typing. No typos.",
    "rare": "Rare typos (~1 per 5-6 messages). Small, realistic mistakes.",
    "occasional": "Occasional typos (~1 per 3-4 messages). Still readable.",
    "frequent": "Frequent typos (1-2 per message). Still understandable.",
}

CHAT_PUNCTUATION_STYLE_GUIDES: dict[str, str] = {
    "clean": "Use proper, standard punctuation. Keep it correct but not overly formal or 'essay-like'.",
    "minimal": "Use minimal punctuation. Often skip ending periods; punctuate only when needed for clarity.",
    "expressive": "Use punctuation to show emphasis and pacing when it fits (!!!, ???, ...).",
    "erratic": "Use punctuation inconsistently: sometimes too much, sometimes too little. Mix styles unpredictably.",
}

CHAT_EMOJI_FREQUENCY_GUIDES: dict[str, str] = {
    "never": "Do not use emojis.",
    "light": "Use emojis lightly (~1 per 5-6 messages).",
    "regular": "Use emojis regularly (1-2 per 2-3 messages).",
    "heavy": "Use emojis frequently (2-4 per message).",
}
