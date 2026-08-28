import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { MemoizedBarsIcon } from "../multi-track-audio-player/MultiTrackAudioPlayer";

const LoadingStateComponent = ({ message, status = null }) => {
  return (
    <Box
      sx={{
        marginY: "auto",
        height: "100%",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        gap: 2,
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          justifyContent: "center",
          alignItems: "center",
          gap: 2,
        }}
      >
        {status === "fetching" && <MemoizedBarsIcon />}

        <Typography typography="s2_1" fontWeight="fontWeightMedium">
          {message}
        </Typography>
      </Box>
    </Box>
  );
};

export default LoadingStateComponent;
LoadingStateComponent.propTypes = {
  message: PropTypes.string,
  status: PropTypes.string,
};
