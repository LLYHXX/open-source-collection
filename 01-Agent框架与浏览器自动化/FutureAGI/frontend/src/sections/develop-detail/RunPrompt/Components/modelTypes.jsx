import { Stack } from "@mui/material";
import CustomTooltip from "../../../../components/tooltip/CustomTooltip";
import SvgColor from "../../../../components/svg-color";

// --- Tooltip messages ---
export const MODEL_TYPE_TOOLTIPS = {
  llm: "Large Language Model — processes and generates natural language text.",
  tts: "Text-to-Speech — converts text input into natural-sounding audio output.",
  stt: "Speech-to-Text — transcribes spoken audio into written text.",
  image:
    "Image Generation — generates images from text prompts using AI models.",
};

// --- Model types with tooltips ---
export const MODEL_TYPES = [
  {
    label: (
      <Stack gap={1} direction="row" alignItems="center">
        LLM{" "}
        <CustomTooltip size="small" title={MODEL_TYPE_TOOLTIPS.llm} show>
          <SvgColor
            sx={{ height: 12, width: 12 }}
            src="/assets/icons/ic_info.svg"
          />
        </CustomTooltip>
      </Stack>
    ),
    value: "llm",
  },
  {
    label: (
      <Stack gap={1} direction="row" alignItems="center">
        Text-to-Speech{" "}
        <CustomTooltip size="small" title={MODEL_TYPE_TOOLTIPS.tts} show>
          <SvgColor
            sx={{ height: 12, width: 12 }}
            src="/assets/icons/ic_info.svg"
          />
        </CustomTooltip>
      </Stack>
    ),
    value: "tts",
  },
  {
    label: (
      <Stack gap={1} direction="row" alignItems="center">
        Speech-to-Text{" "}
        <CustomTooltip size="small" title={MODEL_TYPE_TOOLTIPS.stt} show>
          <SvgColor
            sx={{ height: 12, width: 12 }}
            src="/assets/icons/ic_info.svg"
          />
        </CustomTooltip>
      </Stack>
    ),
    value: "stt",
  },
  {
    label: (
      <Stack gap={1} direction="row" alignItems="center">
        Image Generation{" "}
        <CustomTooltip size="small" title={MODEL_TYPE_TOOLTIPS.image} show>
          <SvgColor
            sx={{ height: 12, width: 12 }}
            src="/assets/icons/ic_info.svg"
          />
        </CustomTooltip>
      </Stack>
    ),
    value: "image",
  },
];
