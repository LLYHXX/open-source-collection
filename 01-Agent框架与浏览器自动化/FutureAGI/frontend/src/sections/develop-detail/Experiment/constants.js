import { PromptRoles } from "src/utils/constants";
import { getRandomId } from "src/utils/utils";

export const PROMPT_CONFIG_TYPE = {
  PROMPT: "prompt",
  AGENT: "agent",
};

export const PROMPT_CONFIG_TYPES = [
  {
    label: "Prompt",
    value: PROMPT_CONFIG_TYPE.PROMPT,
    icon: "/assets/icons/navbar/ic_prompt.svg",
  },
  {
    label: "Agent",
    value: PROMPT_CONFIG_TYPE.AGENT,
    icon: "/assets/icons/navbar/ic_agents.svg",
  },
];

export const experimentCreationSteps = [
  {
    id: "basic-info",
    title: "Basic Info",
  },
  {
    id: "configuration",
    title: "Configuration",
  },
  {
    id: "evaluations",
    title: "Evaluations",
  },
];

export const experimentTypeOptions = [
  {
    label: "LLM",
    value: "llm",
    subtitle: "Process and generate natural language text",
    icon: "/assets/icons/ic_icon_llm.svg",
  },
  {
    label: "TTS",
    value: "tts",
    subtitle: "Converting text into natural sounding audio",
    icon: "/assets/icons/ic_icon_tts.svg",
  },
  {
    label: "STT",
    value: "stt",
    subtitle: "Transcribe spoken audio into written text",
    icon: "/assets/icons/ic_icon_stt.svg",
  },
  {
    label: "Image",
    value: "image",
    subtitle: "Transcribe spoken audio into written text",
    icon: "/assets/icons/ic_image.svg",
  },
];

export const getOutputOptions = {
  llm: [
    { label: "Text", value: "string" },
    { label: "json", value: "json" },
  ],
  stt: [
    { label: "Text", value: "string" },
    { label: "json", value: "json" },
  ],
  tts: [{ label: "Audio", value: "audio" }],
  image: [{ label: "Image", value: "image" }],
};

export const DEFAULT_MESSAGES = [
  {
    id: getRandomId(),
    role: PromptRoles.SYSTEM,
    content: [
      {
        type: "text",
        text: "",
      },
    ],
  },
  {
    id: getRandomId(),
    role: PromptRoles.USER,
    content: [
      {
        type: "text",
        text: "",
      },
    ],
  },
];
