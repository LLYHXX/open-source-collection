import { Box, Checkbox, MenuItem, Popover, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo } from "react";
import { useEvaluationList } from "src/api/develop/develop-detail";
import FormSearchField from "src/components/FormSearchField/FormSearchField";
import { useDebounce } from "src/hooks/use-debounce";

const EvalsSelectDropDown = React.forwardRef(
  ({ open, onClose, multiple, onSelect, searchText, setSearchText }, ref) => {
    const debouncedSearchText = useDebounce(searchText.trim(), 500);

    const { data: evalList } = useEvaluationList(debouncedSearchText);

    const evalOptions = useMemo(
      () =>
        evalList?.map(({ id, name }) => ({
          label: name,
          value: id,
        })),
      [evalList],
    );

    return (
      <Popover
        open={open}
        anchorEl={ref.current}
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
            minWidth: ref.current?.clientWidth,
          },
        }}
      >
        <Box>
          <FormSearchField
            placeholder="Search evaluation"
            size="small"
            searchQuery={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            fullWidth
          />
          <Typography
            sx={{ paddingX: 1, paddingTop: 1 }}
            color="text.disabled"
            fontWeight={600}
            fontSize={12}
          >
            All Evaluations
          </Typography>
          <Box sx={{ maxHeight: "220px", overflowY: "auto" }}>
            {evalOptions?.length > 0 &&
              evalOptions?.map((option) => (
                <MenuItem
                  key={option.value}
                  value={option.value}
                  onClick={() => onSelect(option)}
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

EvalsSelectDropDown.displayName = "EvalsSelectDropDown";

EvalsSelectDropDown.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  multiple: PropTypes.bool,
  onSelect: PropTypes.func,
  setSearchText: PropTypes.func,
  searchText: PropTypes.string,
};

export default EvalsSelectDropDown;
