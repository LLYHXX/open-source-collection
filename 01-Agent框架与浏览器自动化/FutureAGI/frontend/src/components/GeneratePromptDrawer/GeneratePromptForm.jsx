import { Box, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import FormTextFieldV2 from "../FormTextField/FormTextFieldV2";
export default function GeneratePromptForm({
  onSubmit,
  control,
  placeholder = "Describe your task...",
  rows = 8,
  disabled,
}) {
  const theme = useTheme();
  return (
    <Box>
      <form onSubmit={onSubmit}>
        <FormTextFieldV2
          control={control}
          multiline
          disabled={disabled}
          rows={rows}
          placeholder={placeholder}
          fullWidth
          fieldName="prompt"
          sx={{
            backgroundColor: "action.hover",
            borderRadius: `${theme.spacing(0.5)} !important`,
            padding: "0px",
            "& .MuiOutlinedInput-root": {
              borderRadius: `${theme.spacing(0.5)} !important`,
              padding: theme.spacing(2),
              typography: "s1",
              color: "text.primary",
              fontWeight: "fontWeightRegular",
              "& fieldset": {
                border: "1px solid",
                borderColor: "divider",
                borderRadius: theme.spacing(0.5),
              },
              "&:hover fieldset": {
                borderColor: "divider",
              },
              "&.Mui-focused fieldset": {
                borderColor: "divider",
              },
              "&:hover": {
                outline: "none",
              },
              "&.Mui-focused": {
                outline: "none",
                boxShadow: "none",
              },
              "& textarea::placeholder": {
                color: "text.disabled",
                typography: "s1",
                fontWeight: "fontWeightRegular",
              },
            },
          }}
        />
      </form>
    </Box>
  );
}

GeneratePromptForm.propTypes = {
  onSubmit: PropTypes.func,
  control: PropTypes.object,
  placeholder: PropTypes.string,
  rows: PropTypes.number,
  disabled: PropTypes.bool,
};
