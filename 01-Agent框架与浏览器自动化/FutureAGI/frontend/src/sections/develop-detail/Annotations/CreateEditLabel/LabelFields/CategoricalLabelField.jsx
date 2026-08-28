import { Box, Checkbox, FormControlLabel, Radio } from "@mui/material";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { Controller } from "react-hook-form";

const CategoricalInput = ({ settings, values, setValues }) => {
  const normalizedValues = React.useMemo(() => {
    if (Array.isArray(values)) return values;
    if (typeof values === "string") {
      try {
        const parsed = JSON.parse(values);
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    }
    return [];
  }, [values]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {settings.options.map(({ value, id }) => (
        <FormControlLabel
          key={id}
          sx={{ marginLeft: 0 }}
          control={
            settings.multiChoice ? (
              <Checkbox
                checked={normalizedValues?.includes(value)}
                onChange={(_, checked) => {
                  if (checked) {
                    setValues([...normalizedValues, value]);
                  } else {
                    setValues(normalizedValues.filter((v) => v !== value));
                  }
                }}
                size="small"
                inputProps={{ "aria-label": "controlled" }}
                sx={{
                  padding: 1,
                  py: 0.5,
                  color: "grey.400",
                  "&.Mui-checked": {
                    color: "primary.main",
                  },
                }}
              />
            ) : (
              <Radio
                checked={Boolean(values?.includes(value))}
                onChange={() => {
                  setValues([value]);
                }}
                sx={{ marginRight: 1, paddingY: 0.5 }}
                size="small"
                inputProps={{ "aria-label": "controlled" }}
              />
            )
          }
          label={value}
          labelPlacement="end"
        />
      ))}
    </Box>
  );
};

CategoricalInput.propTypes = {
  settings: PropTypes.object,
  values: PropTypes.array,
  setValues: PropTypes.func,
};

const CategoricalLabelField = ({ control, fieldName, settings }) => {
  const [value, setValue] = useState([]);

  return (
    <Box
      sx={{ width: "100%", display: "flex", flexDirection: "column", mb: 1 }}
    >
      {control ? (
        <>
          <Controller
            control={control}
            name={fieldName}
            render={({ field }) => (
              <CategoricalInput
                settings={settings}
                values={field.value}
                setValues={field.onChange}
              />
            )}
          />
        </>
      ) : (
        <CategoricalInput
          settings={settings}
          values={value}
          setValues={setValue}
        />
      )}
    </Box>
  );
};

CategoricalLabelField.propTypes = {
  control: PropTypes.object,
  label: PropTypes.string,
  fieldName: PropTypes.string,
  settings: PropTypes.object,
};

export default CategoricalLabelField;
