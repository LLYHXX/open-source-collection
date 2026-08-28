import { FormControl, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { FormSearchSelectFieldState } from "src/components/FromSearchSelectField";

const BooleanFilterOperators = [
  { label: "Passed", value: "true" },
  { label: "Failed", value: "false" },
];

const DevelopBooleanFilter = ({ filter, updateFilter }) => {
  return (
    <>
      <Typography variant="body2">is</Typography>
      <FormControl size="small" sx={{ minWidth: "100px" }}>
        <FormSearchSelectFieldState
          label="Value"
          showClear={false}
          size="small"
          value={filter.filterConfig.filterValue}
          options={BooleanFilterOperators}
          onChange={(e) => {
            updateFilter(filter.id, (internalFilter) => ({
              ...internalFilter,
              filterConfig: {
                ...internalFilter.filterConfig,
                filterValue: e.target.value,
              },
            }));
          }}
        />
      </FormControl>
    </>
  );
};

DevelopBooleanFilter.propTypes = {
  filter: PropTypes.object,
  updateFilter: PropTypes.func,
};

export default DevelopBooleanFilter;
