import z from "zod";

export const CreateOptimizationValidation = z.object({
  name: z
    .string({ message: "Optimization Name is required" })
    .min(1, "Optimization name is required"),
  startDate: z.date({ message: "Start Date is required" }),
  endDate: z.date({ message: "Start Date is required" }),
  optimizeType: z
    .string({ message: "Please select a optimization type." })
    .min(1, "Please select a optimization type"),
  environment: z.number({
    message: "Please select a environment",
    invalid_type_error: "Please select a environment",
  }),
  version: z
    .string({ message: "Please select a version" })
    .min(1, "Please select a version"),
  metrics: z
    .array(z.object({ label: z.string(), value: z.string() }), {
      message: "Please select a metric",
    })
    .min(1, "Please select a metric"),
});
