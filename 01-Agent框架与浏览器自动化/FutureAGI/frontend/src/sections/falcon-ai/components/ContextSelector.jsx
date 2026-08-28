import React, { useState } from "react";
import ButtonBase from "@mui/material/ButtonBase";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import { alpha, useTheme } from "@mui/material/styles";
import Iconify from "src/components/iconify";
import useFalconStore from "../store/useFalconStore";

const CONTEXT_OPTIONS = [
  { value: "auto", label: "Auto", icon: "mdi:auto-fix" },
  { value: "datasets", label: "Datasets", icon: "mdi:database-outline" },
  {
    value: "evaluations",
    label: "Evaluations",
    icon: "mdi:clipboard-check-outline",
  },
  { value: "tracing", label: "Tracing", icon: "mdi:chart-timeline-variant" },
  { value: "experiments", label: "Experiments", icon: "mdi:flask-outline" },
  { value: "agents", label: "Agents", icon: "mdi:robot-outline" },
  { value: "prompts", label: "Prompts", icon: "mdi:text-box-outline" },
];

export default function ContextSelector() {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";
  const [anchorEl, setAnchorEl] = useState(null);

  const selectedContext = useFalconStore((s) => s.selectedContext);
  const setSelectedContext = useFalconStore((s) => s.setSelectedContext);

  const open = Boolean(anchorEl);
  const current =
    CONTEXT_OPTIONS.find((o) => o.value === selectedContext) ||
    CONTEXT_OPTIONS[0];

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleSelect = (value) => {
    setSelectedContext(value);
    setAnchorEl(null);
  };

  return (
    <>
      <ButtonBase
        onClick={handleClick}
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 0.5,
          px: 1,
          py: 0.5,
          borderRadius: "10px",
          border: 1,
          borderColor: isDark
            ? alpha(theme.palette.common.white, 0.1)
            : alpha(theme.palette.common.black, 0.1),
          bgcolor: isDark
            ? alpha(theme.palette.common.white, 0.04)
            : alpha(theme.palette.common.black, 0.03),
          transition: "all 0.15s ease",
          "&:hover": {
            borderColor: isDark
              ? alpha(theme.palette.common.white, 0.2)
              : alpha(theme.palette.common.black, 0.2),
            bgcolor: isDark
              ? alpha(theme.palette.common.white, 0.08)
              : alpha(theme.palette.common.black, 0.05),
          },
        }}
      >
        <Iconify
          icon={current.icon}
          width={14}
          sx={{ color: "text.secondary" }}
        />
        <Typography
          sx={{
            fontSize: 12,
            fontWeight: 500,
            color: "text.secondary",
            lineHeight: 1,
            whiteSpace: "nowrap",
          }}
        >
          {current.label}
        </Typography>
        <Iconify
          icon="mdi:chevron-down"
          width={14}
          sx={{ color: "text.disabled", ml: -0.25 }}
        />
      </ButtonBase>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "top", horizontal: "left" }}
        transformOrigin={{ vertical: "bottom", horizontal: "left" }}
        slotProps={{
          paper: {
            sx: {
              minWidth: 200,
              maxHeight: 380,
              mt: -0.5,
              borderRadius: "12px",
              border: 1,
              borderColor: "divider",
              boxShadow: isDark
                ? `0 8px 24px ${alpha(theme.palette.common.black, 0.4)}`
                : `0 8px 24px ${alpha(theme.palette.common.black, 0.12)}`,
            },
          },
        }}
      >
        {CONTEXT_OPTIONS.map((option) => (
          <MenuItem
            key={option.value}
            onClick={() => handleSelect(option.value)}
            selected={selectedContext === option.value}
            sx={{
              py: 1,
              px: 2,
              borderRadius: "8px",
              mx: 0.5,
              "&.Mui-selected": {
                bgcolor: isDark
                  ? alpha(theme.palette.common.white, 0.08)
                  : alpha(theme.palette.primary.main, 0.08),
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 28 }}>
              <Iconify
                icon={option.icon}
                width={18}
                sx={{ color: "text.secondary" }}
              />
            </ListItemIcon>
            <ListItemText
              primary={option.label}
              primaryTypographyProps={{ fontSize: 13 }}
            />
            {selectedContext === option.value && (
              <Iconify
                icon="mdi:check"
                width={16}
                sx={{ color: "primary.main", ml: 1 }}
              />
            )}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}
