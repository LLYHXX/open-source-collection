import { Box } from "@mui/material";
import React, { useState } from "react";
import MetricsTabGraph from "../../EvaluationsTabs/MetricsTabGraph";
import LogsTabGrid from "./LogsTabGrid";

const EvalsLogTab = () => {
  const [dateFilter, setDateFilter] = useState(null);

  return (
    <Box
      sx={{
        backgroundColor: "background.paper",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflowY: "auto",
      }}
    >
      <Box height="240px">
        <MetricsTabGraph setDateFilter={setDateFilter} />
      </Box>
      <Box height="100%">
        {/* <Box height="calc(100% - 240px)"> */}
        <LogsTabGrid dateFilter={dateFilter} isLog />
      </Box>
    </Box>
  );
};

export default EvalsLogTab;
