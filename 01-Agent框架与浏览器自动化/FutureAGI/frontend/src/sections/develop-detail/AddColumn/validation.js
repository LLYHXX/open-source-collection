import { z } from "zod";

export const AddColumnSchema = z.object({
  newColumnName: z.string().min(1, { message: "Column name is required" }),
  columnType: z.string().min(1, { message: "Column type is required" }),
});
