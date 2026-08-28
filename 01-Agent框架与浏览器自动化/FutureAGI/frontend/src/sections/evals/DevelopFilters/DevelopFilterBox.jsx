import { Box, Collapse } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import DevelopFilterRow from "./DevelopFilterRow";
import { DefaultFilter } from "./common";
import { getRandomId } from "src/utils/utils";

const DevelopFilterBoxChild = ({
  filters,
  setFilters,
  allColumns,
  onClose,
}) => {
  const addFilter = () => {
    setFilters([...filters, { ...DefaultFilter, id: getRandomId() }]);
  };

  const removeFilter = (id) => {
    if (filters.length === 1) {
      onClose();
    }

    setFilters((internalFilters) => {
      if (internalFilters.length === 1) {
        return [DefaultFilter];
      }
      return internalFilters.filter((filter) => filter.id !== id);
    });
  };

  const updateFilter = (id, newFilter) => {
    setFilters((internalFilters) =>
      internalFilters.map((filter) => {
        if (filter.id === id) {
          return typeof newFilter === "function"
            ? newFilter(filter)
            : newFilter;
        } else {
          return filter;
        }
      }),
    );
  };

  return (
    <Box
      sx={{
        paddingBottom: "12px",
        display: "flex",
        flexDirection: "column",
        gap: 0.5,
      }}
    >
      <Box
        sx={{
          border: "2px solid",
          borderRadius: "8px",
          borderColor: "divider",
          padding: 2,
          gap: 1,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {filters.map((filter, index) => (
          <DevelopFilterRow
            key={filter.id}
            index={index}
            removeFilter={removeFilter}
            addFilter={addFilter}
            filter={filter}
            allColumns={allColumns}
            updateFilter={updateFilter}
          />
        ))}
      </Box>
    </Box>
  );
};

DevelopFilterBoxChild.propTypes = {
  onHideFilter: PropTypes.func,
  filters: PropTypes.array,
  setFilters: PropTypes.func,
  allColumns: PropTypes.array,
  onClose: PropTypes.func,
};

const DevelopFilterBox = ({
  setDevelopFilterOpen,
  developFilterOpen,
  filters,
  setFilters,
  allColumns,
}) => {
  return (
    <Collapse in={developFilterOpen} orientation="vertical">
      <DevelopFilterBoxChild
        onHideFilter={() => setDevelopFilterOpen(false)}
        filters={filters}
        setFilters={setFilters}
        allColumns={allColumns}
        onClose={() => setDevelopFilterOpen(false)}
      />
    </Collapse>
  );
};

DevelopFilterBox.propTypes = {
  setDevelopFilterOpen: PropTypes.func,
  developFilterOpen: PropTypes.bool,
  filters: PropTypes.array,
  setFilters: PropTypes.func,
  allColumns: PropTypes.array,
};

export default DevelopFilterBox;
