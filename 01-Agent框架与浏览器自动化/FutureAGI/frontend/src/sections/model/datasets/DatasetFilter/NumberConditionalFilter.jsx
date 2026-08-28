import {
  FormControl,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const NumberOptions = [
  { label: "Equal", value: "equal" },
  { label: "Not Equal", value: "notEqual" },
  { label: "Greater than", value: "greaterThan" },
  { label: "Greater than or equal to", value: "greaterThanEqualTo" },
  { label: "Less than", value: "lessThan" },
  { label: "Less than or equal to", value: "lessThanEqualTo" },
  { label: "Between", value: "between" },
  { label: "Not between", value: "notBetween" },
];

const NumberConditionalFilter = ({ filter, setValue }) => {
  return (
    <>
      <FormControl size="small">
        <Select
          value={filter.operator}
          onChange={(e) => {
            const newValue = e.target.value;
            setValue({
              operator: newValue,
            });
          }}
        >
          {NumberOptions.map(({ label, value }) => (
            <MenuItem value={value} key={value}>
              {label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <TextField
        sx={{ width: "80px" }}
        type="number"
        placeholder="Value"
        size="small"
        value={filter?.value?.[0] || ""}
        onChange={(e) =>
          setValue({
            value:
              filter?.value.length > 0
                ? filter?.value?.map((v, idx) => {
                    if (idx === 0) {
                      return e.target.value;
                    }
                    return v;
                  })
                : [e.target.value],
          })
        }
      />
      {["between", "notBetween"].includes(filter.operator) ? (
        <>
          <Typography variant="body2" color="text.disabled">
            and
          </Typography>
          <TextField
            sx={{ width: "80px" }}
            type="number"
            placeholder="Value"
            size="small"
            value={filter?.value?.[1] || ""}
            onChange={(e) =>
              setValue({
                value:
                  filter?.value.length > 1
                    ? filter?.value?.map((v, idx) => {
                        if (idx === 1) {
                          return e.target.value;
                        }
                        return v;
                      })
                    : [filter?.value?.[0], e.target.value],
              })
            }
          />
        </>
      ) : (
        <></>
      )}
    </>
  );
};

NumberConditionalFilter.propTypes = {
  filter: PropTypes.object,
  setValue: PropTypes.func,
};

export default NumberConditionalFilter;
