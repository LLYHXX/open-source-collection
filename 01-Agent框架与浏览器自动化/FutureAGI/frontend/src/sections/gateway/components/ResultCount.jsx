import React from "react";
import PropTypes from "prop-types";
import { Typography } from "@mui/material";

const ResultCount = ({ count, singular, plural }) => {
  const label = count === 1 ? singular : plural || `${singular}s`;

  return (
    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
      Showing {count} {label}
    </Typography>
  );
};

ResultCount.propTypes = {
  count: PropTypes.number.isRequired,
  singular: PropTypes.string.isRequired,
  plural: PropTypes.string,
};

export default ResultCount;
