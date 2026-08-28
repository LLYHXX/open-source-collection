import { z } from "zod";

export const formSchema = z.object({
  name: z.string().min(1, "This field is required"),
  prompt: z.string().min(1, "This field is required"),
  model: z.string().min(1, "This field is required"),
  agentType: z.string().min(1, "This field is required"),
  llmTemperature: z.number().nonnegative().min(0, "This field is required"),
  voiceProvider: z.string().optional(),
  voiceName: z.string().optional(),
  interruptSensitivity: z.preprocess(
    (val) => (val === "" ? undefined : Number(val)),
    z.number().nonnegative().optional(),
  ),
  conversationSpeed: z.preprocess(
    (val) => (val === "" ? undefined : Number(val)),
    z.number().nonnegative().optional(),
  ),
  finishedSpeakingSensitivity: z.preprocess(
    (val) => (val === "" ? undefined : Number(val)),
    z.number().nonnegative().optional(),
  ),
  maxCallDurationInMinutes: z.preprocess(
    (val) => (val === "" ? undefined : Number(val)),
    z.number().nonnegative().optional(),
  ),
  initialMessageDelay: z.preprocess(
    (val) => (val === "" ? undefined : Number(val)),
    z.number().optional(),
  ),
  initialMessage: z.string().optional(),
});
