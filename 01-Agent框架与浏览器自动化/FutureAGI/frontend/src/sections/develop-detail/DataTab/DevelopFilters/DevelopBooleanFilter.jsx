import { Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { FormSearchSelectFieldState } from "src/components/FromSearchSelectField";

const BooleanFilterOperators = [
  { label: "True", value: "true" },
  { label: "False", value: "false" },
];

const DevelopBooleanFilter = ({ filter, updateFilter }) => {
  return (
    <>
      <Typography variant="body2">is</Typography>
      <FormSearchSelectFieldState
        onChange={(e) => {
          updateFilter(filter.id, (internalFilter) => ({
            ...internalFilter,
            filterConfig: {
              ...internalFilter.filterConfig,
              filterValue: e.target.value,
            },
          }));
        }}
        value={filter.filterConfig.filterValue}
        label="Value"
        size="small"
        options={BooleanFilterOperators.map(({ label, value }) => ({
          label,
          value,
        }))}
      />
    </>
  );
};

DevelopBooleanFilter.propTypes = {
  filter: PropTypes.object,
  updateFilter: PropTypes.func,
};

export default DevelopBooleanFilter;
