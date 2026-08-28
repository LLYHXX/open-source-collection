import _ from "lodash";
import { camelCaseToTitleCase } from "src/utils/utils";

export const personaSettings = {
  name: {
    icon: "/assets/icons/persona/ic_name.svg",
    label: "Name",
  },
  gender: {
    icon: "/assets/icons/persona/person.svg",
    label: "Gender",
  },
  ageGroup: {
    icon: "/assets/icons/persona/ic_age_groups.svg",
    label: "Age Group",
  },
  location: {
    icon: "/assets/icons/persona/ic_location.svg",
    label: "Location",
  },
  profession: {
    icon: "/assets/icons/persona/profession.svg",
    label: "Profession",
  },
  language: {
    icon: "/assets/icons/persona/language.svg",
    label: "Language",
  },
  accent: {
    icon: "/assets/icons/persona/accent.svg",
    label: "Accent",
  },
  personality: {
    icon: "/assets/icons/persona/ic_personality.svg",
    label: "Personality",
  },
  communicationStyle: {
    icon: "/assets/icons/persona/ic_communication_style.svg",
    label: "Communication Style",
  },
  tone: {
    icon: "/assets/icons/persona/ic_communication_style.svg",
    label: "Tone", //communicationStyle
  },
  verbosity: {
    icon: "/assets/icons/persona/ic_speaking_sensitivity.svg",
    label: "Verbosity", //finishedSpeakingSensitivity
  },
  regionalMix: {
    icon: "/assets/icons/persona/ic_regionalMix.svg",
    label: "Regional Mix",
  },
  slangUsage: {
    icon: "/assets/icons/persona/ic_speaking_sensitivity.svg",
    label: "Slang Usage", //finishedSpeakingSensitivity
  },
  typosFrequency: {
    icon: "/assets/icons/persona/ic_typo_frequency.svg",
    label: "Typos Frequency",
  },
  punctuation: {
    icon: "/assets/icons/persona/ic_punctuation.svg",
    label: "Punctuation",
  },
  emojiUsage: {
    icon: "/assets/icons/persona/ic_emoji_usage.svg",
    label: "Emoji Usage",
  },
  conversationSpeed: {
    icon: "/assets/icons/persona/ic_speaking_sensitivity.svg", //finishedSpeakingSensitivity
    label: "Conversation Speed",
  },
  backgroundSound: {
    icon: "/assets/icons/persona/language.svg",
    label: "Background Sound",
  },
  finishedSpeakingSensitivity: {
    icon: "/assets/icons/persona/ic_speaking_sensitivity.svg",
    label: "Finished Speaking Sensitivity",
  },
  interruptSensitivity: {
    icon: "/assets/icons/persona/ic_interupt_sensitivity.svg",
    label: "Interrupt Sensitivity",
  },
};
export const getPersonaIconAndLabel = (key) => {
  const camelCasedKey = _.camelCase(key.replace(/_/g, " "));
  return (
    personaSettings[camelCasedKey] || {
      icon: "/assets/icons/ic_info.svg",
      label: camelCaseToTitleCase(camelCasedKey),
    }
  );
};
