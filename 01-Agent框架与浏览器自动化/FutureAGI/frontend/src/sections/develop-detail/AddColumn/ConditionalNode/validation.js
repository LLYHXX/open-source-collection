import { z } from "zod";
import { messageSuperRefineFunction } from "../../Common/validation";

const stringToIntSchema = (errorMessage) => {
  return z.string({
    required_error: errorMessage,
  });
};

const MessageValidationSchema = z.object({
  // id: z.string(),
  role: z.enum(["user", "assistant", "system"]),
  content: z.string().refine((str) => str.length > 1, "Content is required"),
});

export const getConditionalNodeValidation = (allColumns) => {
  return z.object({
    type: z.string().optional(),
    new_column_name: z.string().min(1, "New column name is required"),
    config: z
      .array(
        z.object({
          branch_type: z.enum(["if", "elif", "else"]),
          condition: z.string(),
          branch_node_config: z.object({
            type: z.string().min(1, "Column type is required"),
            config: z.object({
              // name: z.string().optional(),
              model: z.string().optional(),
              outputFormat: z
                .enum(["string", "array", "number", "object"])
                .optional(),
              messages: z
                .array(MessageValidationSchema)
                .superRefine(messageSuperRefineFunction)
                .optional(),
              responseFormat: z
                .enum(["text", "json_object"])
                .nullable()
                .optional(),
              temperature: z.number().min(0).max(2).nullable().optional(),
              topP: z.number().min(0).max(2).nullable().optional(),
              maxTokens: z.number().min(1).max(128000).nullable().optional(),
              presencePenalty: z.number().min(-2).max(2).nullable().optional(),
              frequencyPenalty: z.number().min(-2).max(2).nullable().optional(),
              toolChoice: z.enum(["auto", "required", "none"]).optional(),
              tools: z
                .array(z.any())
                .transform((val) => val.map((t) => ({ id: t.tool.value })))
                .superRefine((data, ctx) => {
                  const toolChoice = data.toolChoice;
                  if (
                    (toolChoice === "required" || toolChoice === "auto") &&
                    data.tools.length === 0
                  ) {
                    ctx.addIssue({
                      code: z.ZodIssueCode.custom,
                      message:
                        "At least one tool is required when tool choice is required or auto",
                      path: ["tools"],
                    });
                  }
                })
                .optional(),
              subType: z
                .enum(["pinecone", "qdrant", "weaviate", "retrieval"])
                .optional(),
              apiKey: z.string().optional(),
              indexName: z.string().optional(),
              namespace: z.string().optional(),
              topK: stringToIntSchema().optional(),
              queryKey: z.string().optional(),
              embeddingConfig: z
                .object({
                  model: z.string().optional(),
                  type: z.string().optional(),
                })
                .optional(),
              // .superRefine((data, ctx) => {
              //   if (data.model?.length > 0 || data.type?.length > 0) {
              //     if (!data.model?.length) {
              //       ctx.addIssue({
              //         code: z.ZodIssueCode.custom,
              //         message: "Model is required",
              //         path: ["model"],
              //       });
              //     }
              //     if (!data.type?.length) {
              //       ctx.addIssue({
              //         code: z.ZodIssueCode.custom,
              //         message: "Type is required",
              //         path: ["type"],
              //       });
              //     }
              //   }
              // }),
              searchType: z.string().optional(),
              key: z.string().optional(),
              vectorLength: stringToIntSchema().optional(),
              collectionName: z.string().optional(),
              jsonKey: z.string().optional(),
              // newColumnName: z.string().optional(),
              code: z.string().optional(),
              column_id: z.string().optional(),
              instruction: z.string().optional(),
              language_model_id: z.string().optional(),
              // columnName: z.string().optional(),
              url: z.string().url("Invalid URL").optional(),
              method: z.string().optional(),
              labels: z
                .array(
                  z.object({
                    id: z.string().optional(),
                    value: z.string().optional(),
                  }),
                )
                .transform((t) => t.map((e) => e.value))
                .optional(),
              params: z
                .object({
                  id: z.string().optional(),
                  name: z.string().min(1, "Key is required").optional(),
                  value: z.string().min(1, "Value is required").optional(),
                  type: z.string().min(1, "Type is required").optional(),
                })
                .optional()
                .default({}),

              headers: z
                .object({
                  id: z.string().optional(),
                  name: z.string().min(1, "Key is required").optional(),
                  value: z.string().min(1, "Value is required").optional(),
                  type: z.string().min(1, "Type is required").optional(),
                })
                .optional()
                .default({}),
              body: z
                .string()

                .transform((v) => {
                  let content = v;

                  allColumns.forEach(({ headerName, field }) => {
                    const pattern = new RegExp(
                      `{{\\s*${headerName}\\s*}}`,
                      "g",
                    );
                    content = content.replace(pattern, `{{${field}}}`);
                  });

                  return content;
                })
                .refine((value) => {
                  if (!value?.length) return true;
                  try {
                    JSON.parse(value);
                    return true;
                  } catch (e) {
                    return false;
                  }
                }, "Invalid JSON format")
                .transform((value) => {
                  if (!value?.length) return {};
                  return JSON.parse(value);
                })
                .optional()
                .default("{}"),
              outputType: z.string().optional(),
              concurrency: z
                .number()
                .positive("Concurrency must be a positive integer")
                .optional(), // Optional field
            }),
            // .passthrough(), // Allow additional fields that might be specific to other node types
          }),
        }),
      )
      .min(1, "At least one branch is required")
      .superRefine((branches, ctx) => {
        branches.forEach((branch, index) => {
          if (
            (branch.branch_type === "if" || branch.branch_type === "elif") &&
            (!branch.condition || branch.condition.trim() === "")
          ) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: "Condition is required ",
              path: [index, "condition"],
            });
          }
        });
      }),
  });
};
