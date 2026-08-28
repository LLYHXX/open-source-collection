import React, { useMemo } from "react";
import { Box, Typography, useTheme } from "@mui/material";
import { FormCodeEditor } from "../form-code-editor";
import { ShowComponent } from "../show";
import { editorOptions } from "./KeysHelper";
import PropTypes from "prop-types";
import FormTextFieldV2 from "../FormTextField/FormTextFieldV2";
import "react-json-view-lite/dist/index.css";
import "./ApiKeyForm.css";

const APIKeyForm = ({
  control,
  onFocusInput = () => {},
  onKeyDown = () => {},
  fieldName = "key",
  isJsonKey = false,
  showJsonField = true,
  label = "API Key",
  placeholder = "",
  onChange = () => {},
  required = false,
  size = "small",
  fullWidth = true,
  disabled = false,
  ...restProps
}) => {
  const theme = useTheme();

  const formWrapperStyles = useMemo(
    () => ({
      width: "100%",
      display: "flex",
      flexDirection: "column",
      gap: theme.spacing(2),
    }),
    [theme],
  );

  return (
    <Box>
      <Box sx={formWrapperStyles}>
        <ShowComponent condition={showJsonField && !isJsonKey}>
          <FormTextFieldV2
            control={control}
            fieldName={fieldName}
            label={label}
            placeholder={placeholder}
            onChange={onChange}
            onFocus={onFocusInput}
            onKeyDown={onKeyDown}
            required={required}
            size={size}
            fullWidth={fullWidth}
            helperText=""
            defaultValue=""
            onBlur={() => {}}
            disabled={disabled}
            {...restProps}
          />
        </ShowComponent>

        <ShowComponent condition={showJsonField && isJsonKey}>
          <>
            {placeholder && (
              <Typography
                variant="s1"
                fontWeight="fontWeightRegular"
                color="text.primary"
              >
                {placeholder}
              </Typography>
            )}
            <FormCodeEditor
              editorOptions={editorOptions}
              height="250px"
              defaultLanguage="json"
              options={{
                lineNumbers: "off",
                lineDecorationsWidth: 0,
                lineNumbersMinChars: 2,
                glyphMargin: false,
              }}
              theme={
                theme.palette.mode === "dark" ? "vs-dark" : "xcode-default"
              }
              language="json"
              control={control}
              fieldName={fieldName}
              className="json-editor"
              helperText=""
              showError={true}
              onFocusInput={onFocusInput}
              sx={{ width: "100%" }}
            />
          </>
        </ShowComponent>
      </Box>
    </Box>
  );
};

APIKeyForm.propTypes = {
  control: PropTypes.object,
  onFocusInput: PropTypes.func,
  onKeyDown: PropTypes.func,
  fieldName: PropTypes.string,
  isJsonKey: PropTypes.bool,
  showJsonField: PropTypes.bool,
  label: PropTypes.string,
  onChange: PropTypes.func,
  placeholder: PropTypes.string,
  required: PropTypes.bool,
  size: PropTypes.string,
  fullWidth: PropTypes.bool,
  sx: PropTypes.object,
  disabled: PropTypes.bool,
};

export default APIKeyForm;
