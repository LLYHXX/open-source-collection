import PropTypes from "prop-types";
import { Chip } from "@mui/material";

const STATUS_CONFIG = {
  draft: { label: "Draft", color: "default" },
  active: { label: "Active", color: "info" },
  paused: { label: "Paused", color: "warning" },
  completed: { label: "Completed", color: "success" },
};

StatusBadge.propTypes = {
  status: PropTypes.string,
};

export default function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.draft;
  return (
    <Chip
      label={config.label}
      color={config.color}
      size="small"
      variant="soft"
    />
  );
}
