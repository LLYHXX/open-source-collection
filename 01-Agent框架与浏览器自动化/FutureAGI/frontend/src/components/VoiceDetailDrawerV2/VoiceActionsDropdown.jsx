import React, { useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  ButtonBase,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
} from "@mui/material";
import Iconify from "src/components/iconify";

export const VOICE_ACTIONS = [
  { id: "annotate", label: "Annotate", icon: "mdi:comment-text-outline" },
  { id: "queue", label: "Add to annotation queue", icon: "mdi:playlist-plus" },
  { id: "dataset", label: "Move to dataset", icon: "mdi:database-outline" },
  { id: "tags", label: "Add tags", icon: "mdi:tag-outline" },
  { id: "download", label: "Download raw data", icon: "mdi:download-outline" },
];

const VoiceActionsDropdown = ({ onAction, actions = VOICE_ACTIONS }) => {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef(null);

  return (
    <>
      <ButtonBase
        ref={anchorRef}
        data-voice-actions-button
        onClick={() => setOpen((prev) => !prev)}
        sx={{
          display: "inline-flex",
          alignItems: "center",
          gap: 0.5,
          height: 24,
          px: 1,
          border: "1px solid",
          borderColor: "divider",
          borderRadius: "4px",
          bgcolor: "background.paper",
          fontSize: 11,
          fontWeight: 500,
          fontFamily: "'Inter', sans-serif",
          color: "text.primary",
          whiteSpace: "nowrap",
          flexShrink: 0,
          "&:hover": {
            bgcolor: "background.neutral",
            borderColor: "text.disabled",
          },
        }}
      >
        <Iconify icon="mdi:lightning-bolt-outline" width={13} />
        <span>Actions</span>
        <Iconify icon="mdi:chevron-down" width={12} />
      </ButtonBase>

      <Menu
        open={open}
        anchorEl={anchorRef.current}
        onClose={() => setOpen(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              minWidth: 220,
              mt: 0.5,
              boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
              borderRadius: "6px",
              "& .MuiMenuItem-root": { fontSize: 12, py: 0.75, px: 1.25 },
            },
          },
        }}
      >
        {actions.map((a) => (
          <MenuItem
            key={a.id}
            onClick={() => {
              setOpen(false);
              onAction?.(a.id);
            }}
            dense
          >
            <ListItemIcon sx={{ minWidth: 0, mr: 1 }}>
              <Iconify icon={a.icon} width={15} />
            </ListItemIcon>
            <ListItemText
              primaryTypographyProps={{ fontSize: 12, fontWeight: 500 }}
            >
              {a.label}
            </ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </>
  );
};

VoiceActionsDropdown.propTypes = {
  onAction: PropTypes.func,
  actions: PropTypes.array,
};

export default VoiceActionsDropdown;
