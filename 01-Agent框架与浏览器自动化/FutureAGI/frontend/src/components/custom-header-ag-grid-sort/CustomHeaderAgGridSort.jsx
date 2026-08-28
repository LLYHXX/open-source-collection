import PropTypes from "prop-types";
import React, { forwardRef, useEffect, useState } from "react";
import SvgColor from "src/components/svg-color";

const CustomHeaderAgGridSort = forwardRef((props, ref) => {
  const { column, setSort } = props;
  const [sortIcon, setSortIcon] = useState(null);

  const getSort = () => column?.getSort();

  const onSortChanged = () => {
    const sort = getSort();
    setSortIcon(
      !sort
        ? null
        : sort === "asc"
          ? "ascending-sort-ag-grid"
          : "descending-sort-ag-grid",
    );
  };

  const onSortRequested = (order, event) => {
    setSort(order, event.shiftKey);
  };

  const handleSort = (event) => {
    if (column?.colDef?.sortable) {
      const currentSort = getSort();
      const newSortOrder = !currentSort
        ? "asc"
        : currentSort === "asc"
          ? "desc"
          : null;
      onSortRequested(newSortOrder, event);
    }
  };

  useEffect(() => {
    if (ref.current) {
      ref.current.addEventListener("click", handleSort);
    }
    return () => {
      ref?.current?.removeEventListener("click", handleSort);
    };
  }, [ref]);

  useEffect(() => {
    column?.addEventListener("sortChanged", onSortChanged);
    onSortChanged();
  }, []);

  return sortIcon ? (
    <SvgColor
      src={`/assets/icons/${sortIcon}.svg`}
      sx={{ width: "16px", height: "16px", color: "text.secondary" }}
    />
  ) : null;
});

CustomHeaderAgGridSort.displayName = " CustomHeaderAgGridSort";

export default CustomHeaderAgGridSort;

CustomHeaderAgGridSort.propTypes = {
  column: PropTypes.object,
  setSort: PropTypes.func,
};
