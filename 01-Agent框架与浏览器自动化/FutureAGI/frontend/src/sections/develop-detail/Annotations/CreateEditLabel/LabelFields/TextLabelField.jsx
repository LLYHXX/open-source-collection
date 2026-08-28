import { Box, TextField, Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React, { useCallback, useMemo, useRef, useState } from "react";
import { useWatch } from "react-hook-form";
import FormTextFieldV2 from "src/components/FormTextField/FormTextFieldV2";
import { createTextFieldSchema } from "src/components/traceDetailDrawer/validation/validation";

const ControlTextField = ({
  control,
  fieldName,
  settings,
  showCount,
  error,
}) => {
  const field = useWatch({ control, name: fieldName });
  const maxLength = settings?.maxLength ? settings.maxLength : 100;

  // Capture initial value on first render to detect if already annotated
  const initialValueRef = useRef(field);
  const wasAnnotated =
    initialValueRef.current != null && initialValueRef.current !== "";

  const currentLength = field?.trim()?.length || 0;
  // Show error only when field has content that fails validation,
  // OR the field was already annotated and user cleared it to empty
  const hasError = !!error && (!!field?.trim() || wasAnnotated);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", width: "100%" }}>
      {/* Main field */}
      {showCount(currentLength, maxLength, hasError, true)}
      <FormTextFieldV2
        control={control}
        fieldName={fieldName}
        size="small"
        fullWidth
        multiline
        rows={4}
        placeholder={settings?.placeholder || "Type here"}
      />
    </Box>
  );
};

ControlTextField.propTypes = {
  control: PropTypes.object,
  fieldName: PropTypes.string,
  settings: PropTypes.object,
  showCount: PropTypes.func,
  error: PropTypes.object,
};

const TextLabelField = ({ control, label, fieldName, settings, error }) => {
  const theme = useTheme();
  const [value, setValue] = useState("");
  const isControlled = !!control;
  const hasPlaceholder = settings?.placeholder?.trim() !== "";
  const hasMaxLength = settings?.maxLength?.toString().trim() !== "";

  const uncontrolledSchema = useMemo(() => {
    return createTextFieldSchema(settings);
  }, [settings]);

  const validateUncontrolledValue = useCallback(
    (val) => {
      try {
        uncontrolledSchema.parse(val);
        return { success: true };
      } catch (zodError) {
        return {
          success: false,
          error: zodError.errors[0]?.message || "Validation error",
        };
      }
    },
    [uncontrolledSchema],
  );

  const uncontrolledValidation = useMemo(() => {
    const currentLength = value?.length || 0;
    const maxLength = settings?.maxLength ? settings.maxLength : 100;
    const validation = validateUncontrolledValue(value);

    return {
      hasError: !validation.success,
      getErrorMessage: () => validation.error || "",
      currentLength,
      maxLength,
    };
  }, [value, settings, validateUncontrolledValue]);

  const renderLabelAndCount = (
    currentLength,
    maxLength,
    hasError,
    isControlled = false,
  ) => (
    <Box
      display="flex"
      justifyContent={isControlled ? "flex-end" : "space-between"}
      alignItems="center"
      width="100%"
      mb={0.5}
    >
      {!isControlled && (
        <Typography variant="body2" fontWeight={500}>
          {label}
        </Typography>
      )}
      {hasMaxLength && (
        <Typography
          variant="body2"
          color={
            hasError ? theme.palette.error.main : theme.palette.text.secondary
          }
        >
          {currentLength}/{maxLength}
        </Typography>
      )}
    </Box>
  );

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        gap: theme.spacing(1),
        mb: 1,
      }}
    >
      {isControlled ? (
        <ControlTextField
          control={control}
          fieldName={fieldName}
          settings={settings}
          showCount={renderLabelAndCount}
          error={error}
        />
      ) : (
        <>
          {renderLabelAndCount(
            uncontrolledValidation.currentLength,
            uncontrolledValidation.maxLength || 100,
            uncontrolledValidation.hasError,
            false,
          )}
          <TextField
            fullWidth
            size="small"
            multiline
            rows={4}
            error={uncontrolledValidation.hasError}
            onChange={(e) => {
              const val = e.target.value;
              if (
                !uncontrolledValidation.maxLength ||
                val.length <= uncontrolledValidation.maxLength
              ) {
                setValue(val);
              }
            }}
            inputProps={
              uncontrolledValidation.maxLength
                ? { maxLength: uncontrolledValidation.maxLength }
                : {}
            }
            placeholder={hasPlaceholder ? settings.placeholder : ""}
          />
          {uncontrolledValidation.hasError && (
            <Typography variant="caption" color="error.main">
              {uncontrolledValidation.getErrorMessage()}
            </Typography>
          )}
        </>
      )}
    </Box>
  );
};

TextLabelField.propTypes = {
  control: PropTypes.object,
  label: PropTypes.string,
  fieldName: PropTypes.string,
  settings: PropTypes.object,
  error: PropTypes.object,
};

export default TextLabelField;
