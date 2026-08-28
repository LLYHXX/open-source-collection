import { TextField } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { FormSearchSelectFieldState } from "src/components/FromSearchSelectField";
// 'contains'
// 'not_contains'
// 'equals'
// 'not_equals'
// 'starts_with'
// 'ends_with'
// 'in'
// 'not_in'
const TextFilterOperators = [
  { label: "Contains", value: "contains" },
  { label: "Not Contain", value: "not_contains" },
  { label: "Equals", value: "equals" },
  { label: "Not Equals", value: "not_equals" },
  { label: "Starts With", value: "starts_with" },
  { label: "Ends With", value: "ends_with" },
  // { label: "In", value: "in" },
  // { label: "Not In", value: "not_in" },
];

const DevelopTextFilter = ({ filter, updateFilter }) => {
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
        options={TextFilterOperators.map(({ label, value }) => ({
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

DevelopTextFilter.propTypes = {
  filter: PropTypes.object,
  updateFilter: PropTypes.func,
};

export default DevelopTextFilter;
