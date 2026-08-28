import { Box, Typography } from "@mui/material";

import SvgColor from "src/components/svg-color";

const headerComponentLabels = ({ displayName, isAverage = false }) => {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        gap: 0.5,
        overflow: "hidden",
      }}
    >
      <SvgColor
        sx={{ width: "16px" }}
        src={
          isAverage
            ? "/assets/icons/ic_average.svg"
            : "/assets/icons/ic_single_person.svg"
        }
      />
      <Typography
        typography={"s2_1"}
        fontWeight={"fontWeightMedium"}
        sx={{
          textOverflow: "ellipsis",
          overflow: "hidden",
          whiteSpace: "nowrap",
        }}
      >
        {displayName}
      </Typography>
    </Box>
  );
};

export default headerComponentLabels;
