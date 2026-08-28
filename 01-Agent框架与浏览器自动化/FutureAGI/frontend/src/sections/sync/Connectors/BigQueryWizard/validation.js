import z from "zod";

export const TablePermissionValidationSchema = z.object({
  tableId: z
    .string({
      invalid_type_error: "Table Id is required",
      required_error: "Table Id is required",
    })
    .min(1, "Table Id is required"),
  credentialsJson: z
    .string({
      invalid_type_error: "Please upload a valid credential JSON file",
      required_error: "Please upload a valid credential JSON file",
    })
    .min(1, "Please upload a valid credential JSON file"),
});

export const ModelInfoValidationSchema = z.object({
  modelName: z
    .string({
      invalid_type_error: "Model Name is required",
      required_error: "Model Name is required",
    })
    .min(1, "Model Name is required"),
  modelType: z.number({
    invalid_type_error: "Model Type is required",
    required_error: "Model Type is required",
  }),
  environment: z
    .string({
      invalid_type_error: "Environment is required",
      required_error: "Environment is required",
    })
    .min(1, "Environment is required"),
  version: z
    .string({
      invalid_type_error: "Version is required",
      required_error: "Version is required",
    })
    .min(1, "Version is required"),
});

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
  })
  .superRefine((data, ctx) => {
    data.prompt.forEach((item, index) => {
      if (!item.columnName?.length && index > 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Please select a column name",
          path: ["prompt", index, "columnName"],
        });
      }
    });
    data.response.forEach((item, index) => {
      if (!item.columnName?.length) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Please select a column name",
          path: ["response", index, "columnName"],
        });
      }
    });
  });
