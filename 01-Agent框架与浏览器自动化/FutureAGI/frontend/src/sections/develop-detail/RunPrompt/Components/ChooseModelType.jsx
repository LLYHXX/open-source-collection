import { Stack, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import RadioField from "src/components/RadioField/RadioField";
import { MODEL_TYPES } from "./modelTypes";

export default function ChooseModelType({
  control,
  label = "",
  onChange,
  fieldName = "config.modelType",
  excludeTypes = [],
}) {
  const filteredOptions =
    excludeTypes.length > 0
      ? MODEL_TYPES.filter((type) => !excludeTypes.includes(type.value))
      : MODEL_TYPES;

  return (
    <Stack
      sx={{
        mb: 2.25,
      }}
    >
      <Typography
        typography={"s1"}
        color={"text.primary"}
        fontWeight={"fontWeightMedium"}
      >
        {label}
      </Typography>
      <RadioField
        required={false}
        control={control}
        fieldName={fieldName}
        optionColor={"text.primary"}
        labelColor="text.primary"
        groupSx={{ padding: 0, marginLeft: -1 }}
        options={filteredOptions}
        optionDirection={"row"}
        onChange={onChange}
      />
    </Stack>
  );
}

ChooseModelType.propTypes = {
  control: PropTypes.object,
  label: PropTypes.string,
  onChange: PropTypes.func,
  fieldName: PropTypes.string,
  excludeTypes: PropTypes.array,
};
