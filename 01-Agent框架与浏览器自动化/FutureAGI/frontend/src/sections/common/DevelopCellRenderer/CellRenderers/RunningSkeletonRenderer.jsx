import React from "react";
import PropTypes from "prop-types";
import { Box, Skeleton } from "@mui/material";

const RunningSkeletonRenderer = ({ originType, originOfColumn }) => {
  const isAnnotation = originType === "annotation_label";
  return (
    <Box
      sx={{
        paddingX: 1,
        display: "flex",
        alignItems: "center",
        height: "100%",
      }}
    >
      {isAnnotation ? null : (
        <Skeleton
          sx={{
            width: "100%",
            height: originOfColumn ? "80%" : "20px",
            backgroundColor: "background.neutral",
          }}
          variant={originOfColumn ? "rectangular" : "rounded"}
        />
      )}
    </Box>
  );
};

RunningSkeletonRenderer.propTypes = {
  originType: PropTypes.string,
  originOfColumn: PropTypes.bool,
};

export default React.memo(RunningSkeletonRenderer);
