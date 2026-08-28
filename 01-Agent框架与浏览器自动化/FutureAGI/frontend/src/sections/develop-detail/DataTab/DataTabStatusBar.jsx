import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React, { useCallback, useEffect, useState } from "react";
import { useDevelopDetailContext } from "../Context/DevelopDetailContext";

const DataTabStatusBar = () => {
  const [loadedRows, setLoadedRows] = useState(0);
  const [totalRows, setTotalRows] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const { gridApi } = useDevelopDetailContext();
  const api = gridApi.current;

  const getVisibleRowCount = useCallback(() => {
    if (!api) return 0;
    const lastDisplayedRow = api.getLastDisplayedRowIndex();
    return lastDisplayedRow + 1;
  }, [api]);

  const updateRowCount = useCallback(() => {
    if (!api) return;
    const context = api?.getGridOption?.("context");
    const total = context?.totalRowCount ?? api.getDisplayedRowCount();
    setTotalRows(total);
    setLoadedRows(getVisibleRowCount());

    if (context?.totalRowCount !== undefined) {
      setIsLoading(false);
    }
  }, [api, getVisibleRowCount]);

  useEffect(() => {
    if (!api) return;

    // Initial update
    updateRowCount();

    // Listen to grid events that affect visible rows
    const events = [
      "modelUpdated", // Fires on data changes, filtering, sorting
      "bodyScroll", // Fires on scroll - gives real-time feedback
      "viewportChanged", // Fires when viewport changes
      "firstDataRendered", // Fires when first data is rendered
    ];

    events.forEach((event) => {
      api.addEventListener(event, updateRowCount);
    });

    // Subscribe to grid updates
    return () => {
      if (!api.isDestroyed()) {
        events.forEach((event) => {
          api.removeEventListener(event, updateRowCount);
        });
      }
    };
  }, [api, getVisibleRowCount, updateRowCount]);

  return (
    <Box sx={{ padding: 1, display: "flex", alignItems: "center", gap: 1 }}>
      {isLoading ? (
        <>{/* add loading if needed */}</>
      ) : (
        <span>
          Showing Rows: {loadedRows} / Total Rows: {totalRows || 0}
        </span>
      )}
    </Box>
  );
};

DataTabStatusBar.propTypes = {
  api: PropTypes.object,
  context: PropTypes.object,
};

export default DataTabStatusBar;
