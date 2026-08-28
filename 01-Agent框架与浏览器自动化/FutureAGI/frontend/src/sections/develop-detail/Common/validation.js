import { z } from "zod";
import _ from "lodash";

export const messageSuperRefineFunction = (messages, ctx) => {
  const systemPromptIndex = messages.findIndex((msg) => msg.role === "system");

  const lastMessage = messages?.[messages.length - 1];

  if (lastMessage?.role !== "user") {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Last prompt must have role 'user'",
      path: [`${messages.length - 1}.content`],
    });
  }

  if (systemPromptIndex > 0 && systemPromptIndex !== 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "System prompt should be first",
      path: [`${systemPromptIndex}.content`],
    });
  }
};
