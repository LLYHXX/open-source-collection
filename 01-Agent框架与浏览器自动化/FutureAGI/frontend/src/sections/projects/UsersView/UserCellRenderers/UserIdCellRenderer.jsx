import React from "react";
import PropTypes from "prop-types";
import { Typography } from "@mui/material";

const UserIdCellRenderer = ({ data }) => {
  const userId = data?.user_id;
  if (!userId) return null;
  return (
    <Typography
      variant="s1"
      fontWeight="fontWeightMedium"
      color="text.primary"
      sx={{
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }}
    >
      {userId}
    </Typography>
  );
};

UserIdCellRenderer.propTypes = {
  data: PropTypes.object.isRequired,
};

export default UserIdCellRenderer;
