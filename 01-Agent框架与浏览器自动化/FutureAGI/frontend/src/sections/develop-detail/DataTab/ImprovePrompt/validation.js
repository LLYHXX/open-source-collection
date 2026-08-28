import { z } from "zod";

export const improvePromptValidationSchema = z.object({
  // explanation: z
  //   .string({
  //     required_error: "Right Value is required",
  //   })
  //   .min(1, {
  //     message: "Right Value is required",
  //   }),
  promptType: z.string({
    required_error: "Improved Value is required",
  }),
  improvement_requirements: z.string({
    required_error: "Improved Value is required",
  }),
  userPrompt: z.object({
    // id: z.string(),
    role: z.string(),
    content: z.string(),
  }),
});
