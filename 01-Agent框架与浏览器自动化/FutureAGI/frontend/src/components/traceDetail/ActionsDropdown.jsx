import React, { useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Button,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
} from "@mui/material";
import Iconify from "src/components/iconify";

const ACTIONS = [
  { id: "dataset", label: "Move to dataset", icon: "mdi:folder-move-outline" },
  {
    id: "prompt-workbench",
    label: "Iterate in prompt workbench",
    icon: "mdi:pencil-outline",
  },
  // {
  //   id: "agent-playground",
  //   label: "Iterate in agent playground",
  //   icon: "mdi:robot-outline",
  // },
  { id: "tags", label: "Add Tags", icon: "mdi:tag-outline" },
  { id: "annotate", label: "Annotate", icon: "mdi:pencil-box-outline" },
  {
    id: "annotation-queue",
    label: "Add to annotation queue",
    icon: "mdi:clipboard-list-outline",
  },
];

const ActionsDropdown = ({ onAction }) => {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef(null);

  return (
    <>
      <Button
        ref={anchorRef}
        variant="outlined"
        size="small"
        endIcon={<Iconify icon="mdi:chevron-down" width={14} />}
        onClick={() => setOpen(true)}
        sx={{
          textTransform: "none",
          fontSize: 12,
          fontWeight: 500,
          height: 30,
          borderColor: "divider",
          color: "text.primary",
        }}
      >
        Actions
      </Button>

      <Menu
        open={open}
        anchorEl={anchorRef.current}
        onClose={() => setOpen(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{ paper: { sx: { minWidth: 240, mt: 0.5 } } }}
      >
        {ACTIONS.map((action) => (
          <MenuItem
            key={action.id}
            onClick={() => {
              setOpen(false);
              onAction?.(action.id);
            }}
            dense
          >
            <ListItemIcon>
              <Iconify icon={action.icon} width={18} />
            </ListItemIcon>
            <ListItemText
              primaryTypographyProps={{ variant: "body2", fontSize: 13 }}
            >
              {action.label}
            </ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </>
  );
};

ActionsDropdown.propTypes = {
  onAction: PropTypes.func,
};

export default React.memo(ActionsDropdown);
