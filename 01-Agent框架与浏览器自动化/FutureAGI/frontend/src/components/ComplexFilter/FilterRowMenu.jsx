import { Box, Checkbox, MenuItem, Popover } from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo, useState } from "react";
import { useDebounce } from "src/hooks/use-debounce";
import FormSearchField from "../FormSearchField/FormSearchField";

const FilterRowMenu = React.forwardRef(
  ({ open, onClose, multiple, onSelect, data }, ref) => {
    const [searchText, setSearchText] = useState("");

    const debouncedSearchText = useDebounce(searchText.trim(), 500);

    const filteredData = useMemo(() => {
      if (!debouncedSearchText.trim()) return data;

      return data.filter((item) =>
        item.label.toLowerCase().includes(debouncedSearchText.toLowerCase()),
      );
    }, [data, debouncedSearchText]);

    const handleSelect = (value) => {
      onSelect(value);
      onClose();
    };

    return (
      <Popover
        open={open}
        anchorEl={ref?.current}
        onClose={onClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
        PaperProps={{
          sx: {
            minWidth: ref?.current?.clientWidth,
          },
        }}
      >
        <Box
          sx={{
            p: 1,
          }}
        >
          <FormSearchField
            placeholder="Search"
            size="small"
            searchQuery={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            sx={{
              mb: 0.5,
              "& .MuiOutlinedInput-root": {
                margin: 0,
                paddingLeft: 1,
              },
            }}
            fullWidth
          />
          <Box sx={{ maxHeight: "220px", overflowY: "auto" }}>
            {filteredData?.map((option) => (
              <MenuItem
                key={option.value}
                value={option.value}
                onClick={() => handleSelect(option)}
              >
                {multiple && <Checkbox />}
                {option.label}
              </MenuItem>
            ))}
          </Box>
        </Box>
      </Popover>
    );
  },
);

FilterRowMenu.displayName = "FilterRowMenu";

FilterRowMenu.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  multiple: PropTypes.bool,
  onSelect: PropTypes.func,
  data: PropTypes.array,
};

export default FilterRowMenu;
