import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const StringConditionalFilter = ({ options, setValue, filter }) => {
  return (
    <>
      <Typography color="text.disabled" variant="body2">
        is
      </Typography>
      <FormControl sx={{ width: "264px" }} size="small">
        <InputLabel>Select Option</InputLabel>
        <Select
          value={filter?.value?.[0] || ""}
          onChange={(e) => {
            const newValue = e.target.value;
            setValue({
              value: [newValue],
            });
          }}
          label="Select Option"
          MenuProps={{
            sx: {
              maxHeight: "250px",
            },
          }}
        >
          {options.map(({ label, value }) => (
            <MenuItem value={value} key={value}>
              {label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </>
  );
};

StringConditionalFilter.propTypes = {
  options: PropTypes.array,
  filter: PropTypes.object,
  setValue: PropTypes.func,
};

export default StringConditionalFilter;
