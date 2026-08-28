import { z } from "zod";

export const MappingValidationSchema = z
  .object({
    conversationId: z
      .string({
        invalid_type_error: "Conversation ID column name is required",
        required_error: "Conversation ID column name is required",
      })
      .min(1, "Conversation ID column name is required"),
    timestamp: z
      .string({
        invalid_type_error: "Timestamp column name is required",
        required_error: "Timestamp column name is required",
      })
      .min(1, "Timestamp column name is required"),
    prompt: z.array(
      z.object({
        columnName: z.string(),
        type: z.string(),
      }),
    ),
    response: z.array(
      z.object({
        columnName: z.string(),
        type: z.string(),
      }),
    ),
    modelType: z.string(),
    promptTemplate: z.string(),
    context: z.string(),
    variables: z.array(z.string()),
  })
  .superRefine((data, ctx) => {
    data.prompt.forEach((item, index) => {
      if (!item.columnName?.length) {
        if (data.modelType === "GenerativeImage" && index === 0) {
          return;
        }
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Please select a column name",
          path: ["prompt", index, "columnName"],
        });
      }
    });
    data.response.forEach((item, index) => {
      if (!item.columnName?.length) {
        if (data.modelType === "GenerativeImage" && index === 0) {
          return;
        }
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Please select a column name",
          path: ["response", index, "columnName"],
        });
      }
    });
  });
