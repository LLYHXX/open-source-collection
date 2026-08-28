import React from "react";
import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { format, isValid } from "date-fns";
import CustomTooltip from "src/components/tooltip";
const OptimizationNameRenderer = ({ value }) => {
  return (
    <CustomTooltip title={value?.title} arrow size="small" type="black">
      <Box display="flex" flexDirection="column" sx={{ paddingY: 1 }}>
        <Typography
          typography="s1"
          fontWeight="fontWeightMedium"
          sx={{
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            width: "100%",
          }}
        >
          {value?.title}
        </Typography>
        {value.startedAt && isValid(new Date(value.startedAt)) ? (
          <Typography typography="s3">
            {`Started at ${format(new Date(value.startedAt), "dd-MM-yyyy, HH:mm")}`}
          </Typography>
        ) : (
          "-"
        )}
      </Box>
    </CustomTooltip>
  );
};

OptimizationNameRenderer.propTypes = {
  value: PropTypes.object,
};

export default OptimizationNameRenderer;
