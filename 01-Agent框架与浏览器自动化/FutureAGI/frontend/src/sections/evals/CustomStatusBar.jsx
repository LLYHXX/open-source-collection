import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";

const CustomStatusBar = ({ api }) => {
  const [count, setCount] = useState(0);

  const updateStatusBar = () => {
    setCount(api.getDisplayedRowCount());
  };

  useEffect(() => {
    api.addEventListener("modelUpdated", updateStatusBar);

    // Remove event listener when destroyed
    return () => {
      if (!api.isDestroyed()) {
        api.removeEventListener("modelUpdated", updateStatusBar);
      }
    };
  }, []);

  const getComponent = () => {
    return <Box>Total Rows : {count}</Box>;
  };

  return <Box sx={{ padding: 1 }}>{getComponent()}</Box>;
};

CustomStatusBar.displayName = "CustomStatusBar";

CustomStatusBar.propTypes = {
  api: PropTypes.object,
};

export default CustomStatusBar;
