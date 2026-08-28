import React from "react";
import { Box, Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import FormTextFieldV2 from "../FormTextField/FormTextFieldV2";

const FormTextLabelField = ({
  label,
  labelStyle = {},
  disabled = false,
  ...rest
}) => {
  const theme = useTheme();
  return (
    <Box sx={{ width: "100%" }}>
      {label && (
        <Typography
          fontWeight={"fontWeightMedium"}
          color="text.disabled"
          variant="s2"
          sx={{
            letterSpacing: "0.02em",
            marginBottom: "10px",
            ...labelStyle,
          }}
        >
          {label}
        </Typography>
      )}
      <FormTextFieldV2
        {...rest}
        fullWidth
        hiddenLabel
        disabled={disabled}
        labelStyle={labelStyle}
        sx={{ borderRadius: (theme) => theme.spacing(1) }}
        InputProps={{
          sx: {
            backgroundColor: disabled
              ? "background.paper"
              : theme.palette.background.default,
          },
        }}
      />
    </Box>
  );
};

export default FormTextLabelField;

FormTextLabelField.propTypes = {
  label: PropTypes.string,
  labelStyle: PropTypes.object,
  disabled: PropTypes.bool,
};
