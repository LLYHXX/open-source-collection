import PropTypes from "prop-types";
import React from "react";
import DevelopTextFilter from "./DevelopTextFilter";
import DevelopNumberFilter from "./DevelopNumberFilter";
import DevelopBooleanFilter from "./DevelopBooleanFilter";
import DevelopDateTimeFilter from "./DevelopDateTimeFilter";
import DevelopArrayFilter from "./DevelopArrayFilter";

const DevelopFilterValue = ({ filter, updateFilter }) => {
  switch (filter?.filterConfig?.filterType) {
    case "text":
      return <DevelopTextFilter filter={filter} updateFilter={updateFilter} />;
    case "number":
      return (
        <DevelopNumberFilter filter={filter} updateFilter={updateFilter} />
      );
    case "boolean":
      return (
        <DevelopBooleanFilter filter={filter} updateFilter={updateFilter} />
      );
    case "datetime":
      return (
        <DevelopDateTimeFilter filter={filter} updateFilter={updateFilter} />
      );
    case "array":
      return <DevelopArrayFilter filter={filter} updateFilter={updateFilter} />;
    default:
      return <></>;
  }
};

DevelopFilterValue.propTypes = {
  filter: PropTypes.object,
  updateFilter: PropTypes.func,
};

export default DevelopFilterValue;
