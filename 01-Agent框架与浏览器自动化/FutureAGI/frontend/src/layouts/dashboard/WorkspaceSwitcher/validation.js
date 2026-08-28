import { z } from "zod";

export const CreateWorkspaceValidation = z.object({
  name: z.string().min(1, "Workspace name is required"),
});
