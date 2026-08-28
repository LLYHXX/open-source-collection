import { Chip } from "@mui/material";
import PropTypes from "prop-types";

const TYPE_CONFIG = {
  single: { label: "Single", icon: "circle" },
  composite: { label: "Composite", icon: "layers" },
};

const TypeBadge = ({ type = "single" }) => {
  const config = TYPE_CONFIG[type] || TYPE_CONFIG.single;

  return (
    <Chip
      label={config.label}
      size="small"
      variant="outlined"
      sx={{
        fontSize: "12px",
        height: "22px",
        borderRadius: "4px",
        borderColor: "divider",
        color: "text.secondary",
        "& .MuiChip-label": {
          px: 1,
        },
      }}
    />
  );
};

TypeBadge.propTypes = {
  type: PropTypes.oneOf(["single", "composite"]),
};

export default TypeBadge;
