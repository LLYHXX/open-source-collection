import { useEffect, useState } from "react";
import PropTypes from "prop-types";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Box from "@mui/material/Box";

import axios, { endpoints } from "src/utils/axios";

export default function RegionSelect({ sx }) {
  const [config, setConfig] = useState(null);

  useEffect(() => {
    axios
      .get(endpoints.auth.config)
      .then(({ data }) => setConfig(data.result))
      .catch(() => {});
  }, []);

  if (
    !config?.cloud ||
    !config.availableRegions?.length ||
    config.availableRegions.length <= 1
  )
    return null;

  const handleChange = (e) => {
    const selected = config.availableRegions.find(
      (r) => r.code === e.target.value,
    );
    if (selected && selected.code !== config.region) {
      const { pathname, search, hash } = window.location;
      window.location.href = `${selected.appUrl}${pathname}${search}${hash}`;
    }
  };

  return (
    <Box sx={{ mb: 2, ...sx }}>
      <FormControl fullWidth size="small">
        <InputLabel>Data Region</InputLabel>
        <Select
          value={config.region || ""}
          onChange={handleChange}
          label="Data Region"
        >
          {config.availableRegions.map((r) => (
            <MenuItem key={r.code} value={r.code}>
              {r.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}

RegionSelect.propTypes = {
  sx: PropTypes.object,
};
