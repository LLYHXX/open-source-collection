import { Box, Collapse, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import DevelopFilterRow from "src/sections/develop-detail/DataTab/DevelopFilters/DevelopFilterRow";
import { DefaultFilter } from "src/sections/develop-detail/DataTab/DevelopFilters/common";
import { getRandomId } from "src/utils/utils";

const RunInsightsFilterChild = ({ filters, setFilters, allColumns }) => {
  const addFilter = () => {
    setFilters([...filters, { ...DefaultFilter, id: getRandomId() }]);
  };

  const removeFilter = (id) => {
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
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Typography fontWeight={700} fontSize="16px" color="text.disabled">
          Filter
        </Typography>
      </Box>
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

RunInsightsFilterChild.propTypes = {
  filters: PropTypes.array,
  setFilters: PropTypes.func,
  allColumns: PropTypes.array,
};

const RunInsightsFilterBox = ({
  developFilterOpen,
  filters,
  setFilters,
  allColumns,
}) => {
  return (
    <Collapse in={developFilterOpen} orientation="vertical">
      <RunInsightsFilterChild
        filters={filters}
        setFilters={setFilters}
        allColumns={allColumns}
      />
    </Collapse>
  );
};

RunInsightsFilterBox.propTypes = {
  developFilterOpen: PropTypes.bool,
  filters: PropTypes.array,
  setFilters: PropTypes.func,
  allColumns: PropTypes.array,
};

export default RunInsightsFilterBox;
