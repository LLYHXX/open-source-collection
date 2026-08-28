import { FormControl, InputLabel, Select } from "@mui/material";
import PropTypes from "prop-types";
import React, { useRef, useState } from "react";

const CustomSelect = ({ popoverComponent = () => null, label, ...rest }) => {
  const [open, setOpen] = useState(false);

  const ref = useRef(null);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <>
      <FormControl size={rest.size}>
        <InputLabel>{label}</InputLabel>
        <Select
          open={open}
          onOpen={handleOpen}
          onClose={handleClose}
          label={label}
          ref={ref}
          sx={{
            minWidth: "150px",
          }}
          MenuProps={{
            PaperProps: {
              style: {
                display: "none",
              },
            },
          }}
          {...rest}
        ></Select>
      </FormControl>
      {popoverComponent({
        open,
        onClose: handleClose,
        anchorElement: ref?.current,
      })}
    </>
  );
};

CustomSelect.propTypes = {
  popoverComponent: PropTypes.func,
  label: PropTypes.string,
};

export default CustomSelect;
