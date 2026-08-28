import z from "zod";

export const DatasetCreateValidation = z.object({
  environment: z
    .string({
      invalid_type_error: "Environment is required.",
      required_error: "Environment is required.",
      message: "Environment is required.",
    })
    .min(1, "Environment is required."),
  version: z
    .string({
      invalid_type_error: "Version is required.",
      required_error: "Version is required.",
      message: "Version is required.",
    })
    .min(1, "Version is required."),
});
