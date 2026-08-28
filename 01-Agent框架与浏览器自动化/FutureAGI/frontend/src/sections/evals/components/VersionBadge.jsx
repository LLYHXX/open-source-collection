import { Chip } from "@mui/material";
import PropTypes from "prop-types";

const VersionBadge = ({ version = "V1" }) => (
  <Chip
    label={version}
    size="small"
    sx={{
      fontSize: "12px",
      fontWeight: 600,
      height: "22px",
      borderRadius: "4px",
      backgroundColor: (theme) =>
        theme.palette.mode === "dark"
          ? "rgba(124, 77, 255, 0.16)"
          : "rgba(124, 77, 255, 0.08)",
      color: (theme) => (theme.palette.mode === "dark" ? "#B794F6" : "#7C4DFF"),
      "&:hover": {
        backgroundColor: (theme) =>
          theme.palette.mode === "dark"
            ? "rgba(124, 77, 255, 0.28)"
            : "rgba(124, 77, 255, 0.16)",
      },
      "& .MuiChip-label": {
        px: 1,
      },
    }}
  />
);

VersionBadge.propTypes = {
  version: PropTypes.string,
};

export default VersionBadge;
