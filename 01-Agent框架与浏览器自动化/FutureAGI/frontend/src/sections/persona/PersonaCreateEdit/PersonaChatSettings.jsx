import { Box, Stack } from "@mui/material";
import React from "react";
import { useFormContext } from "react-hook-form";
import {
  CustomPersonaAccordion,
  CustomPersonaAccordionContent,
  CustomPersonaAccordionHeader,
} from "./PersonCustomComponents";
import SvgColor from "src/components/svg-color";
import LanguageSelector from "./LanguageSelector";
import PropTypes from "prop-types";
import { chatOptionSettings } from "./common";
import ReusableRadioFieldComponent from "./ReusableRadioFieldComponent";

export const PersonaChatSettings = ({ multiple = true }) => {
  const { control } = useFormContext();
  return (
    <Box>
      <CustomPersonaAccordion disableGutters defaultExpanded>
        <CustomPersonaAccordionHeader
          expandIcon={
            <SvgColor src="/assets/icons/custom/lucide--chevron-down.svg" />
          }
        >
          Chat Settings
        </CustomPersonaAccordionHeader>
        <CustomPersonaAccordionContent>
          <Stack spacing={2}>
            <LanguageSelector multiple={multiple} />
            <Stack spacing={2}>
              {chatOptionSettings?.map((setting) => (
                <ReusableRadioFieldComponent
                  key={setting?.title}
                  control={control}
                  title={setting?.title}
                  fieldName={setting?.fieldName}
                  options={setting?.options}
                />
              ))}
            </Stack>
          </Stack>
        </CustomPersonaAccordionContent>
      </CustomPersonaAccordion>
    </Box>
  );
};

PersonaChatSettings.propTypes = {
  multiple: PropTypes.bool,
};
