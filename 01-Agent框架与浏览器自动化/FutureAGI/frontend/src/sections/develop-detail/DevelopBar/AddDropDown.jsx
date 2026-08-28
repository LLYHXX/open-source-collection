import { Box, MenuItem, Popover } from "@mui/material";
import PropTypes from "prop-types";
import { trackEvent, Events } from "src/utils/Mixpanel";
import React from "react";

const Options = [
  { label: "Add Rows", value: "add-rows", event: Events.addRowsClicked },
  {
    label: "Add Columns",
    value: "add-columns",
    event: Events.addColumnsClicked,
  },
  // { label: "Import Column from another dataset", value: "import-column" },
  // { label: "Add Synthetic Data", value: "synthetic-data" }
];

const AddDropDown = React.forwardRef(({ open, setOpen, onSelect }, ref) => {
  return (
    <Popover
      anchorEl={ref?.current}
      open={open}
      onClose={() => setOpen(false)}
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
      transformOrigin={{
        vertical: "top",
        horizontal: "right",
      }}
    >
      <Box>
        {Options.map((option) => (
          <MenuItem
            key={option.value}
            value={option.value}
            onClick={() => {
              trackEvent(option.event);
              onSelect(option.value);
            }}
          >
            {option.label}
          </MenuItem>
        ))}
      </Box>
    </Popover>
  );
});

AddDropDown.displayName = "AddDropDown";

AddDropDown.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  onSelect: PropTypes.func.isRequired,
};

export default AddDropDown;
