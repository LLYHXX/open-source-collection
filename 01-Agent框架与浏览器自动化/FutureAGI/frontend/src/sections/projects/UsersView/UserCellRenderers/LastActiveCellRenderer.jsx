import React from "react";
import PropTypes from "prop-types";
import { Tooltip, Typography } from "@mui/material";
import { format, formatDistanceToNow } from "date-fns";

// Single-line relative-time cell. Exact timestamp is shown in the hover
// tooltip. Used for both "First Active" (activated_at) and "Last Active"
// (last_active) columns — the column config provides the raw value.
const LastActiveCellRenderer = ({ value }) => {
  if (!value) return null;
  const date = new Date(value);
  return (
    <Tooltip
      title={format(date, "dd MMM yyyy, HH:mm:ss")}
      placement="top"
      arrow
    >
      <Typography variant="body2" sx={{ cursor: "default" }}>
        {formatDistanceToNow(date, { addSuffix: true })}
      </Typography>
    </Tooltip>
  );
};

LastActiveCellRenderer.propTypes = {
  value: PropTypes.string,
};

export default LastActiveCellRenderer;
