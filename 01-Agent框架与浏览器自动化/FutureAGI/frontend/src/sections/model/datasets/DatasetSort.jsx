import { Menu, MenuItem } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const DatasetSort = ({ open, onClose, anchorEl, sort, setSort }) => {
  return (
    <Menu
      open={open}
      onClose={onClose}
      anchorEl={anchorEl}
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
      transformOrigin={{
        vertical: "top",
        horizontal: "right",
      }}
    >
      <MenuItem
        selected={sort === "asc"}
        onClick={() => {
          setSort("asc");
          onClose();
        }}
      >
        Latest
      </MenuItem>
      <MenuItem
        selected={sort === "desc"}
        onClick={() => {
          setSort("desc");
          onClose();
        }}
      >
        Earliest
      </MenuItem>
    </Menu>
  );
};

DatasetSort.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  anchorEl: PropTypes.any,
  setSort: PropTypes.func,
  sort: PropTypes.string,
};

export default DatasetSort;
