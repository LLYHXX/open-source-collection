import { z } from "zod";

// Zod schema for message validation
const messageSchema = z
  .object({
    type: z.enum(["text", "audio_url", "pdf_url", "image_url"], {
      errorMap: () => ({
        message: "type must be one of: text, audio_url, pdf_url, image_url",
      }),
    }),
    message: z.string().optional(),
    file_name: z.string().optional(),
    fileName: z.string().optional(), // Allow camelCase for normalization
    file_url: z.string().optional(),
    fileUrl: z.string().optional(), // Allow camelCase for normalization
  })
  .superRefine((data, ctx) => {
    if (data.type === "text") {
      if (!data.message || data.message.trim() === "") {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "message is required for text type",
          path: ["message"],
        });
      }
    } else {
      // For non-text types, check file_name and file_url
      const fileName = data.file_name || data.fileName;
      const fileUrl = data.file_url || data.fileUrl;

      if (!fileName || fileName.trim() === "") {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `file_name is required for ${data.type}`,
          path: ["file_name"],
        });
      }

      if (!fileUrl || fileUrl.trim() === "") {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `file_url is required for ${data.type}`,
          path: ["file_url"],
        });
      } else {
        try {
          new URL(fileUrl);
        } catch {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "file_url must be a valid URL",
            path: ["file_url"],
          });
        }
      }
    }
  });

export const messagesArraySchema = z
  .array(messageSchema)
  .min(1, "Data must be an array with at least one message");
