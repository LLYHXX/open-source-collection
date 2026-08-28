import { getNumberValidation } from "src/utils/validation";
import { z } from "zod";

const createTextAnnotationSettingsSchema = (originalMin, originalMax) =>
  z
    .object({
      placeholder: z.string().min(1, "Placeholder is required"),
      maxLength: getNumberValidation("Max length is required", {
        integerOnly: true,
        positive: true,
      }),
      minLength: getNumberValidation("Min length is required", {
        integerOnly: true,
        positive: true,
      }),
    })
    .superRefine((data, ctx) => {
      if (
        data.minLength &&
        data.maxLength &&
        Number(data.minLength) > Number(data.maxLength)
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Min length cannot be greater than max length",
          path: ["minLength"],
        });
      }

      if (
        data.minLength &&
        data.maxLength &&
        Number(data.maxLength) < Number(data.minLength)
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Max length cannot be less than min length",
          path: ["maxLength"],
        });
      }

      if (
        data.minLength &&
        data.maxLength &&
        Number(data.minLength) === Number(data.maxLength)
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Min length cannot be equal to max length",
          path: ["minLength"],
        });
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Max length cannot be equal to min length",
          path: ["maxLength"],
        });
      }

      if (data.maxLength && Number(data.maxLength) > 255) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Max length cannot exceed 255 characters",
          path: ["maxLength"],
        });
      }

      if (originalMin !== undefined && Number(data.minLength) > originalMin) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message:
            "Min cannot be increased while editing — existing annotations may be affected.",
          path: ["minLength"],
        });
      }

      if (originalMax !== undefined && Number(data.maxLength) < originalMax) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message:
            "Max cannot be decreased while editing — existing annotations may be affected.",
          path: ["maxLength"],
        });
      }
    });

const TextAnnotationSettingsSchema = createTextAnnotationSettingsSchema();

const createNumericAnnotationSettingsSchema = (originalMin, originalMax) =>
  z
    .object({
      min: getNumberValidation("Min is required", {
        integerOnly: true,
        zeroAndPositive: true,
      }),
      max: getNumberValidation("Max is required", {
        integerOnly: true,
        positive: true,
      }),
      stepSize: getNumberValidation("Step size is required", {
        integerOnly: true,
        positive: true,
      }),
      displayType: z.string().min(1, "Display type is required"),
    })
    .superRefine((data, ctx) => {
      if (data.stepSize > data.max) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Step size cannot be greater than max value",
          path: ["stepSize"],
        });
      }

      if (data.min && data.max && Number(data.min) > Number(data.max)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Min value cannot be greater than max value",
          path: ["min"],
        });
      }

      if (data.min && data.max && Number(data.max) < Number(data.min)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Max value cannot be less than min value",
          path: ["max"],
        });
      }

      if (data.min && data.max && Number(data.min) === Number(data.max)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Min value cannot be equal to max value",
          path: ["min"],
        });
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Max value cannot be equal to min value",
          path: ["max"],
        });
      }

      if (originalMin !== undefined && Number(data.min) > originalMin) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message:
            "Min cannot be increased while editing — existing annotations may be affected.",
          path: ["min"],
        });
      }

      if (originalMax !== undefined && Number(data.max) < originalMax) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message:
            "Max cannot be decreased while editing — existing annotations may be affected.",
          path: ["max"],
        });
      }
    });

const NumericAnnotationSettingsSchema = createNumericAnnotationSettingsSchema();

const StarAnnotationSettingsSchema = z.object({
  noOfStars: z.literal(5),
});

const CategoricalAnnotationSettingsSchema = z.object({
  options: z
    .array(z.object({ id: z.string(), value: z.string() }))
    .min(1, "At least one option is required")
    .transform((v) => v.map((o) => ({ label: o.value }))),
  multiChoice: z.boolean(),
});

const buildDiscriminatedUnion = (textSettings, numericSettings) =>
  z.discriminatedUnion("type", [
    z.object({
      name: z.string().min(1, "Name is required"),
      type: z.literal("text"),
      description: z.string().optional(),
      settings: textSettings,
    }),
    z.object({
      name: z.string().min(1, "Name is required"),
      type: z.literal("numeric"),
      description: z.string().optional(),
      settings: numericSettings,
    }),
    z.object({
      name: z.string().min(1, "Name is required"),
      type: z.literal("categorical"),
      description: z.string().optional(),
      settings: CategoricalAnnotationSettingsSchema,
    }),
    z.object({
      name: z.string().min(1, "Name is required"),
      type: z.literal("star"),
      description: z.string().optional(),
      settings: StarAnnotationSettingsSchema,
    }),
    z.object({
      name: z.string().min(1, "Name is required"),
      type: z.literal("thumbs_up_down"),
      description: z.string().optional(),
      settings: z.object({}),
    }),
  ]);

export const createCreateEditLabelValidationSchema = (editData) => {
  if (!editData)
    return buildDiscriminatedUnion(
      TextAnnotationSettingsSchema,
      NumericAnnotationSettingsSchema,
    );

  if (editData.type === "text") {
    return buildDiscriminatedUnion(
      createTextAnnotationSettingsSchema(
        Number(editData.settings?.minLength),
        Number(editData.settings?.maxLength),
      ),
      NumericAnnotationSettingsSchema,
    );
  }

  if (editData.type === "numeric") {
    return buildDiscriminatedUnion(
      TextAnnotationSettingsSchema,
      createNumericAnnotationSettingsSchema(
        Number(editData.settings?.min),
        Number(editData.settings?.max),
      ),
    );
  }

  return buildDiscriminatedUnion(
    TextAnnotationSettingsSchema,
    NumericAnnotationSettingsSchema,
  );
};

export const CreateEditLabelValidationSchema = z.discriminatedUnion("type", [
  z.object({
    name: z.string().min(1, "Name is required"),
    type: z.literal("text"),
    description: z.string().optional(),
    settings: TextAnnotationSettingsSchema,
  }),
  z.object({
    name: z.string().min(1, "Name is required"),
    type: z.literal("numeric"),
    description: z.string().optional(),
    settings: NumericAnnotationSettingsSchema,
  }),
  z.object({
    name: z.string().min(1, "Name is required"),
    type: z.literal("categorical"),
    description: z.string().optional(),
    settings: CategoricalAnnotationSettingsSchema,
  }),
  z.object({
    name: z.string().min(1, "Name is required"),
    type: z.literal("star"),
    description: z.string().optional(),
    settings: StarAnnotationSettingsSchema,
  }),
  z.object({
    name: z.string().min(1, "Name is required"),
    type: z.literal("thumbs_up_down"),
    description: z.string().optional(),
    settings: z.object({}),
  }),
]);
