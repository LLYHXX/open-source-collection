import { z } from "zod";

export const UploadFileValidationSchema = z.object({
  name: z.string().min(1, { message: "Name is required" }),
  modelType: z
    .string({ required_error: "Model type is required" })
    .min(1, { message: "Model type is required" }),
  file: z.any().refine((val) => val !== null, {
    message: "File is required",
  }),
});

export const ManuallyCreateDatasetValidationSchema = z.object({
  name: z.string().min(1, { message: "Name is required" }),
  modelType: z
    .string({ required_error: "Model type is required" })
    .min(1, { message: "Model type is required" }),
  number_of_rows: z
    .number({ message: "Number of rows is required" })
    .min(1, { message: "Number of rows must be at least 1" })
    .max(100, { message: "Only 100 rows can be added" })
    .superRefine((val, ctx) => {
      if (isNaN(val)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Number of rows must be a valid number",
        });
      }
      if (val === undefined || val === null || val === "") {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Number of rows is required",
        });
      }
    }),

  number_of_columns: z
    .number({ message: "Number of columns is required" })
    .min(1, { message: "Number of columns must be at least 1" })
    .max(100, { message: "Only 100 columns can be added" })
    .superRefine((val, ctx) => {
      if (isNaN(val)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Number of columns must be a valid number",
        });
      }
      if (val === undefined || val === null || val === "") {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Number of columns is required",
        });
      }
    }),
});

export const ManuallyCreateDatasetValidationSchema2 = z.object({
  name: z.string().min(1, { message: "Name is required" }),
});

export const CloneDevelopDatasetValidationSchema = z.object({
  name: z.string().min(1, { message: "Name is required" }),
  model_type: z
    .string({ required_error: "Model type is required" })
    .min(1, { message: "Model type is required" }),
  new_dataset_id: z
    .string({ required_error: "Dataset is required" })
    .min(1, { message: "Dataset is required" }),
});

export const HuggingFaceDatasetValidationSchema = z.object({
  huggingface_dataset_config: z
    .string()
    .min(1, { message: "Config is required" }),
  huggingface_dataset_split: z
    .string()
    .min(1, { message: "Split is required" }),
  model_type: z
    .string({ required_error: "Model type is required" })
    .min(1, { message: "Model type is required" }),
  new_dataset_name: z.string().min(1, { message: "Name is required" }),
});

export const HuggingFaceDatasetValidationSchema1 = z.object({
  huggingface_dataset_config: z
    .string()
    .min(1, { message: "Config is required" }),
  huggingface_dataset_split: z
    .string()
    .min(1, { message: "Split is required" }),
  name: z.string().min(1, { message: "Name is required" }),
  num_rows: z.coerce
    .number({
      invalid_type_error: "Number of rows is required",
    })
    .min(1, { message: "Number of rows must be at least 1" }),
});

export const HuggingFaceDatasetValidationSchema2 = z.object({
  huggingface_dataset_config: z
    .string()
    .min(1, { message: "Config is required" }),
  huggingface_dataset_split: z
    .string()
    .min(1, { message: "Split is required" }),
  num_rows: z.coerce
    .number({
      invalid_type_error: "Number of rows is required",
    })
    .min(1, { message: "Number of rows must be at least 1" }),
});
