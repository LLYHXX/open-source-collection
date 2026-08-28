import { Box, FormHelperText } from "@mui/material";
import PropTypes from "prop-types";
import React, { useCallback, useEffect, useState } from "react";
import FieldHeader from "./FieldHeader";
import FieldInputText from "./InputFields/FieldInputText";

import { defaultTabValue } from "./constant";
import { ShowComponent } from "../show";
import FieldInputTextControl from "./InputFields/FieldInputTextControl";
import FieldInputImage from "./InputFields/FieldInputImage";
import FieldInputImageControl from "./InputFields/FieldInputImageControl";
import logger from "src/utils/logger";

const errorMessageId = "playground-input-field-error";

const PlaygroundInput = ({
  fieldTitle,
  control,
  typeFieldName,
  valueFieldName,
  setValue = (methodKey, value) => {
    logger.info("dks", methodKey, value);
  },
  errorMessage,
  value,
  onChange,
  inputType,
  showTabs = false,
  ...rest
}) => {
  useEffect(() => {
    if (errorMessage) {
      const errorTarget = document.getElementById(errorMessageId);
      errorTarget?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [errorMessage]);

  const [currentTab, setCurrentTab] = useState(
    inputType || defaultTabValue.Text,
  );
  const [internalState, setInternalState] = useState({
    audio: { url: "", file: null },
    image: { url: "", file: null },
    text: "",
  });

  const handleOnChange = (e) => {
    if (onChange) {
      setInternalState((pre) => ({
        ...pre,
        [currentTab]:
          currentTab == "text" ? e.target.value : { url: e.url, file: e.file },
      }));
      if (currentTab != defaultTabValue.Text) {
        onChange(e);
        return;
      }
      onChange({ type: currentTab, value: e.target.value || "", url: "" });
    }
  };

  const handleCurrentTab = useCallback(
    (val) => {
      if (val !== currentTab) {
        if (control) {
          setValue(
            valueFieldName,
            val === "text" ? internalState[val] : internalState[val].url,
          );
          setValue(typeFieldName, val);
        } else {
          onChange({
            type: val,
            value: val === "text" ? internalState[val] : "",
            url: val !== "text" ? internalState[val].url : "",
          });
        }
        setCurrentTab(val);
      }
    },
    [onChange, currentTab],
  );

  return (
    <>
      <Box
        sx={{
          width: "100%",
          display: "flex",
          flexDirection: "column",
          gap: 1,
          padding: 2,
          borderRadius: "4px",
          border: "1px solid",
          borderColor: errorMessage ? "error.main" : "divider",
          backgroundColor: "background.default",
        }}
      >
        <FieldHeader
          fieldTitle={fieldTitle}
          currentTab={currentTab}
          setCurrentTab={handleCurrentTab}
          showTabs={showTabs}
          type={currentTab}
          errorMessage={errorMessage}
          {...rest}
        />
        <ShowComponent condition={currentTab === defaultTabValue.Text}>
          <ShowComponent condition={Boolean(control)}>
            <FieldInputTextControl
              control={control}
              onChange={(e) =>
                setInternalState((pre) => ({
                  ...pre,
                  [currentTab]: e.target.value,
                }))
              }
              fieldName={valueFieldName}
              placeholder={"Enter text here"}
              type={currentTab}
            />
          </ShowComponent>
          <ShowComponent condition={!control}>
            <FieldInputText
              value={value?.value || ""}
              onChange={handleOnChange}
              placeholder="Enter text here"
            />
          </ShowComponent>
        </ShowComponent>
        <ShowComponent condition={currentTab !== defaultTabValue.Text}>
          <ShowComponent condition={Boolean(control)}>
            <FieldInputImageControl
              control={control}
              onChange={(e) => {
                setInternalState((pre) => ({
                  ...pre,
                  [currentTab]: { url: e.url, file: e.file },
                }));
              }}
              fieldName={valueFieldName}
              type={currentTab}
              internalState={internalState[currentTab]}
            />
          </ShowComponent>
          <ShowComponent condition={!control}>
            <FieldInputImage
              data={value?.url}
              onChange={handleOnChange}
              type={currentTab}
              internalState={internalState[currentTab]}
            />
          </ShowComponent>
        </ShowComponent>
      </Box>
      {errorMessage && (
        <FormHelperText
          sx={{ marginTop: -1, marginLeft: 0 }}
          error={true}
          id={errorMessageId}
        >
          {errorMessage}
        </FormHelperText>
      )}
    </>
  );
};

export default PlaygroundInput;

PlaygroundInput.propTypes = {
  fieldTitle: PropTypes.string,
  control: PropTypes.any,
  typeFieldName: PropTypes.string,
  valueFieldName: PropTypes.string,
  setValue: PropTypes.func,
  onChange: PropTypes.func,
  errorMessage: PropTypes.string,
  inputType: PropTypes.string,
  value: PropTypes.shape({
    type: PropTypes.string,
    value: PropTypes.string,
    url: PropTypes.string,
  }),
  showTabs: PropTypes.bool,
};
