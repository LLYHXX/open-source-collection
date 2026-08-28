import { z } from "zod";

export const HuggingFaceDatasetValidationSchema2 = z.object({
  huggingface_dataset_config: z
    .string()
    .min(1, { message: "Config is required" }),
  huggingface_dataset_split: z
    .string()
    .min(1, { message: "Split is required" }),
  num_rows: z.union([z.number(), z.string()]).optional(),
});
