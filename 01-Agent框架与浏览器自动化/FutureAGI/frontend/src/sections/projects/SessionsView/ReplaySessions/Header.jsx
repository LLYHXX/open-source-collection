import { IconButton, Stack, Typography } from "@mui/material";
import React from "react";
import SvgColor from "../../../../components/svg-color/svg-color";
import PropTypes from "prop-types";
import { useReplaySessionsStoreShallow } from "./store";

export default function Header({ onClose }) {
  const { createdReplay } = useReplaySessionsStoreShallow((s) => ({
    createdReplay: s.createdReplay,
  }));
  const isVoice = createdReplay?.suggestions?.agentType === "voice";
  const title = isVoice ? "Replay Calls" : "Replay Sessions";
  const subtitle = isVoice
    ? "Replay calls to debug your voice agent"
    : "Replay sessions to create a simulation run";

  return (
    <Stack
      direction={"row"}
      alignItems={"flex-start"}
      justifyContent={"space-between"}
    >
      <Stack gap={0}>
        <Typography
          typography={"m2"}
          fontWeight={"fontWeightSemiBold"}
          color={"text.primary"}
        >
          {title}
        </Typography>
        <Typography
          typography={"s1"}
          fontWeight={"fontWeightRegular"}
          color={"text.primary"}
        >
          {subtitle}
        </Typography>
      </Stack>
      <Stack direction={"column"} alignItems={"flex-end"}>
        <Stack direction={"row"} alignItems={"center"} gap={2}>
          {/* <Link
            sx={{
              typography: "s1",
              fontWeight: "fontWeightMedium",
              textDecoration: "underline",
              color: "primary.main",
            }}
            href="#"
          >
            Learn more
          </Link> */}
          <IconButton
            sx={{
              color: "text.primary",
            }}
            onClick={onClose}
            size="small"
          >
            <SvgColor
              sx={{
                width: 24,
                height: 24,
              }}
              src="/assets/icons/ic_close.svg"
            />
          </IconButton>
        </Stack>
      </Stack>
    </Stack>
  );
}

Header.propTypes = {
  onClose: PropTypes.func.isRequired,
};
