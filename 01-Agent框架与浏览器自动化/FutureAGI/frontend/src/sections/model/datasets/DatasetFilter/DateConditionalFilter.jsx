import { FormControl, MenuItem, Select, Typography } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";

const DateOptions = [
  { label: "Equal", value: "equal" },
  { label: "Not Equal", value: "notEqual" },
  { label: "Greater than", value: "greaterThan" },
  { label: "Greater than or equal to", value: "greaterThanEqualTo" },
  { label: "Less than", value: "lessThan" },
  { label: "Less than or equal to", value: "lessThanEqualTo" },
  { label: "Between", value: "between" },
  { label: "Not between", value: "notBetween" },
];

const DateConditionalFilter = ({ filter, setValue }) => {
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
          {DateOptions.map(({ label, value }) => (
            <MenuItem value={value} key={value}>
              {label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <DatePicker
        slotProps={{
          textField: { size: "small" },
        }}
        sx={{ width: "160px" }}
        inputProps={{
          readOnly: true,
        }}
        value={filter?.value?.[0] || null}
        onChange={(v) => {
          setValue({
            value:
              filter?.value.length > 0
                ? filter?.value?.map((v, idx) => {
                    if (idx === 0) {
                      return v;
                    }
                    return v;
                  })
                : [v],
          });
        }}
      />
      {["between", "notBetween"].includes(filter.operator) ? (
        <>
          <Typography variant="body2" color="text.disabled">
            and
          </Typography>
          <DatePicker
            value={filter?.value?.[1] || null}
            slotProps={{
              textField: { size: "small" },
            }}
            onChange={(v) => {
              setValue({
                value:
                  filter?.value.length > 1
                    ? filter?.value?.map((v, idx) => {
                        if (idx === 1) {
                          return v;
                        }
                        return v;
                      })
                    : [filter?.value?.[0], v],
              });
            }}
            sx={{ width: "160px" }}
            inputProps={{
              readOnly: true,
            }}
          />
        </>
      ) : (
        <></>
      )}
    </>
  );
};

DateConditionalFilter.propTypes = {
  filter: PropTypes.object,
  setValue: PropTypes.func,
};

export default DateConditionalFilter;
