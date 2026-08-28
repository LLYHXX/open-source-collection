import { z } from "zod";

// Define the Zod schema
export const AnnotationFormSchema = z
  .object({
    name: z.string().min(1, "Name is required"),
    staticFields: z.array(
      z.object({
        column: z.string().nonempty("Column is required"),
        type: z.string(),
        view: z.string(),
      }),
    ),
    // .min(1, "At least one static field is required")
    responseFields: z.array(
      z.object({
        column: z.string().nonempty("Column is required"),
        type: z.string(),
        edit: z.string(),
      }),
    ),
    // .min(1, "At least one response field is required"),
    labelFields: z
      .array(
        z.object({
          labelName: z.string().nonempty("Label name is required"),
        }),
      )
      .min(1, "At least one label must be added"),
    annotatorFields: z
      .array(
        z.object({
          addAnnotator: z
            .array(z.string().uuid())
            .min(1, "At least one annotator must be added"),
        }),
      )
      .min(1, "At least one annotator is required"),
    responses: z.coerce
      .number()
      .int("Must be an integer")
      .positive("This must be a positive integer")
      .default(1),
  })
  .superRefine((data, ctx) => {
    if (
      (!data.staticFields || data.staticFields.length === 0) &&
      (!data.responseFields || data.responseFields.length === 0)
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          "At least one static field is required if no response field is provided",
        path: ["staticFields"], // Error associated with staticFields
      });

      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          "At least one response field is required if no static field is provided",
        path: ["responseFields"], // Error associated with responseFields
      });
    }
    if (data.responses > data.annotatorFields?.[0]?.addAnnotator?.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          "Number of responses must be less than or equal to number of annotators",
        path: ["responses"],
      });
    }
  });
