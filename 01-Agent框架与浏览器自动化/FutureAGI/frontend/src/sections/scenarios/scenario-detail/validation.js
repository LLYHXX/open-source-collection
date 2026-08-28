import { z } from "zod";

export const AddRowUsingAiValidationSchema = z.object({
  description: z
    .string({ message: "Description is required" })
    .min(1, "Description is required"),
  numRows: z
    .number({ message: "Rows is required" })
    .min(10, "Minimum 10 Rows are required")
    .max(20000, "Maximum 20000 Rows are allowed"),
});
