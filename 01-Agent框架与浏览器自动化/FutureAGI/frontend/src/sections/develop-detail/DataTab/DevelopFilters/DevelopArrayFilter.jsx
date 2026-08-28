import { TextField } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { FormSearchSelectFieldState } from "src/components/FromSearchSelectField";

const ArrayFilterOperators = [
  { label: "Contains", value: "contains" },
  { label: "Not Contain", value: "not_contains" },
];

const DevelopArrayFilter = ({ filter, updateFilter }) => {
  return (
    <>
      <FormSearchSelectFieldState
        onChange={(e) => {
          updateFilter(filter.id, (internalFilter) => ({
            ...internalFilter,
            filterConfig: {
              ...internalFilter.filterConfig,
              filterOp: e.target.value,
            },
          }));
        }}
        value={filter.filterConfig.filterOp}
        label="Operator"
        size="small"
        options={ArrayFilterOperators.map(({ label, value }) => ({
          label,
          value,
        }))}
      />
      <TextField
        size="small"
        label="Value"
        type="text"
        value={filter.filterConfig.filterValue}
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
    </>
  );
};

DevelopArrayFilter.propTypes = {
  filter: PropTypes.object,
  updateFilter: PropTypes.func,
};

export default DevelopArrayFilter;
