import z from "zod";

export const InviteMemberValidation = z.object({
  email: z
    .string()
    .min(1, "User email is required")
    .email("Please enter valid email"),
  organizationRole: z.string().min(1, "Please select a role"),
});
