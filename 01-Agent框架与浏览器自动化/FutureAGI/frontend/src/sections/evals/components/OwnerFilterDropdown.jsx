import { MenuItem, Select } from "@mui/material";
import PropTypes from "prop-types";

const OPTIONS = [
  { value: "all", label: "All Evals" },
  { value: "user", label: "User Built" },
  { value: "system", label: "System Built" },
];

const OwnerFilterDropdown = ({ value = "all", onChange }) => (
  <Select
    size="small"
    value={value}
    onChange={(e) => onChange(e.target.value)}
    sx={{
      fontSize: "13px",
      height: "32px",
      "& .MuiSelect-select": { py: 0.5, px: 1.5 },
      borderColor: "divider",
    }}
  >
    {OPTIONS.map((opt) => (
      <MenuItem key={opt.value} value={opt.value} sx={{ fontSize: "13px" }}>
        {opt.label}
      </MenuItem>
    ))}
  </Select>
);

OwnerFilterDropdown.propTypes = {
  value: PropTypes.oneOf(["all", "user", "system"]),
  onChange: PropTypes.func.isRequired,
};

export default OwnerFilterDropdown;
