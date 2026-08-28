import React from "react";
import PromptModalWrapper from "./PromptModalWrapper";
import PropTypes from "prop-types";
import {
  DialogContent,
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { Controller, useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { FormSelectField } from "src/components/FormSelectField";
import FormTextFieldV2 from "src/components/FormTextField/FormTextFieldV2";

const runPreviewSchema = z
  .object({
    previewFor: z.enum(["firstNRows", "multipleRows"], {
      required_error: "Please select a preview option.",
    }),
    numberOfRows: z
      .string()
      .optional()
      .refine((val) => !val || /^\d+$/.test(val), {
        message: "Please enter a valid number of rows.",
      }),
    rowNumbers: z
      .string()
      .optional()
      .refine(
        (val) => !val || val.split(",").every((n) => /^\d+$/.test(n.trim())),
        {
          message: "Row numbers must be comma-separated integers.",
        },
      ),
  })
  .superRefine((data, ctx) => {
    if (data.previewFor === "firstNRows" && !data.numberOfRows) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["numberOfRows"],
        message: "Please provide the number of rows.",
      });
    }

    if (data.previewFor === "multipleRows" && !data.rowNumbers?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["rowNumbers"],
        message: "Please provide the row numbers.",
      });
    }
  });

export default function RunPreviewModal({ open, onClose, onRun }) {
  const theme = useTheme();
  const {
    control,
    formState: { isValid },
    handleSubmit,
    reset,
  } = useForm({
    defaultValues: {
      previewFor: "firstNRows",
      numberOfRows: "1",
      rowNumbers: "1,2,3,4,5,6",
    },
    resolver: zodResolver(runPreviewSchema),
    mode: "onChange",
  });

  const previewFor = useWatch({ control, name: "previewFor" });

  const onSubmit = (data) => {
    const runData =
      data?.previewFor === "firstNRows"
        ? {
            first_n_rows: Number.parseInt(data?.numberOfRows),
          }
        : {
            row_indices: data?.rowNumbers?.split(",").map((i) => +i),
          };
    onRun(runData);
    reset();
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <PromptModalWrapper
      title="Run preview on custom rows"
      open={open}
      onClose={handleClose}
      isValid={isValid}
      onSubmit={handleSubmit(onSubmit)}
      actionBtnTitle="Run"
    >
      <DialogContent sx={{ padding: 0 }}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormControl fullWidth>
            <Controller
              name="previewFor"
              control={control}
              render={({ field }) => (
                <RadioGroup
                  {...field}
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: theme.spacing(3),
                  }}
                >
                  <FormControlLabel
                    value="firstNRows"
                    sx={{
                      padding: 0,
                      alignItems: "flex-start",
                      "& .MuiFormControlLabel-label": {
                        width: "100%",
                      },
                    }}
                    control={
                      <Radio
                        sx={{
                          padding: 0,
                          paddingLeft: "10px",
                          paddingTop: "4px",
                        }}
                      />
                    }
                    label={
                      <Stack
                        sx={{ pl: "12px" }}
                        direction="column"
                        gap={theme.spacing(0.25)}
                      >
                        <Typography
                          variant="s1"
                          color="text.primary"
                          fontWeight="fontWeightMedium"
                        >
                          First N rows
                        </Typography>
                        <Typography
                          variant="s2"
                          fontWeight="fontWeightRegular"
                          color="text.secondary"
                        >
                          {
                            "Choose how many rows you'd like to preview from the top of your data."
                          }
                        </Typography>
                        {previewFor === "firstNRows" && (
                          <FormSelectField
                            control={control}
                            fieldName="numberOfRows"
                            label="Number of rows"
                            placeholder="Select number of rows"
                            fullWidth
                            size="small"
                            options={Array(10)
                              .fill(0)
                              .map((_, idx) => ({
                                label: String(idx + 1),
                                value: String(idx + 1),
                              }))}
                            sx={{
                              "& .MuiSelect-icon": {
                                color: "text.primary",
                              },
                              mt: theme.spacing(2.5),
                            }}
                          />
                        )}
                      </Stack>
                    }
                  />

                  <FormControlLabel
                    value="multipleRows"
                    sx={{
                      padding: 0,
                      alignItems: "flex-start",
                      "& .MuiFormControlLabel-label": {
                        width: "100%",
                      },
                    }}
                    control={
                      <Radio
                        sx={{
                          padding: 0,
                          paddingLeft: "10px",
                          paddingTop: "4px",
                        }}
                      />
                    }
                    label={
                      <Stack
                        sx={{ pl: "12px" }}
                        direction="column"
                        gap={theme.spacing(0.25)}
                      >
                        <Typography
                          variant="s1"
                          color="text.primary"
                          fontWeight="fontWeightMedium"
                        >
                          Row numbers
                        </Typography>
                        <Typography
                          variant="s2"
                          fontWeight="fontWeightRegular"
                          color="text.secondary"
                        >
                          {"Choose the number of row you want to preview"}
                        </Typography>
                        {previewFor === "multipleRows" && (
                          <FormTextFieldV2
                            fullWidth
                            sx={{
                              mt: theme.spacing(2.5),
                              width: "100%",
                            }}
                            size="small"
                            control={control}
                            fieldName={"rowNumbers"}
                            label={"Add number"}
                            placeholder={"Multiple rows"}
                          />
                        )}
                      </Stack>
                    }
                  />
                </RadioGroup>
              )}
            />
          </FormControl>
        </form>
      </DialogContent>
    </PromptModalWrapper>
  );
}

RunPreviewModal.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  onRun: PropTypes.func,
};
