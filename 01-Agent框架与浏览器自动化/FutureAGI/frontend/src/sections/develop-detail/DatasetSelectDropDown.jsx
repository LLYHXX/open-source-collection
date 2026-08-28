import {
  Box,
  Checkbox,
  MenuItem,
  Popover,
  Typography,
  useTheme,
  CircularProgress,
} from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo, useState } from "react";
import FormSearchField from "src/components/FormSearchField/FormSearchField";
import { useDebounce } from "src/hooks/use-debounce";

const DatasetSelectDropDown = React.forwardRef(
  (
    {
      open,
      onClose,
      multiple,
      onSelect,
      fetchOptions,
      searchPlaceholder,
      labelText,
    },
    ref,
  ) => {
    const [searchText, setSearchText] = useState("");
    const theme = useTheme();

    const debouncedSearchText = useDebounce(searchText.trim(), 500);

    const {
      data: list = [],
      isLoading,
      error,
    } = fetchOptions(debouncedSearchText);

    const options = useMemo(
      () =>
        list?.map(({ id, name, datasetId, scenarioType, dataset }) => ({
          label: name,
          value: id || datasetId,
          scenarioType,
          scenarioDatasetId: dataset,
        })) || [],
      [list],
    );

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
        <Box>
          <FormSearchField
            placeholder={searchPlaceholder || "Search"}
            size="small"
            searchQuery={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            fullWidth
          />
          <Typography
            sx={{ paddingX: theme.spacing(1), paddingTop: theme.spacing(1) }}
            color="text.secondary"
            fontWeight={600}
            fontSize={12}
          >
            {labelText}
          </Typography>
          <Box sx={{ maxHeight: "220px", overflowY: "auto" }}>
            {error ? (
              <Box sx={{ padding: 2, textAlign: "center" }}>
                <Typography color="error" variant="body2">
                  Failed to load datasets
                </Typography>
              </Box>
            ) : isLoading ? (
              <Box
                sx={{
                  padding: 2,
                  textAlign: "center",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 1,
                  height: "30px",
                }}
              >
                <CircularProgress size={20} />
                <Typography variant="body2" color="text.secondary">
                  Loading datasets...
                </Typography>
              </Box>
            ) : options?.length === 0 ? (
              <Box sx={{ padding: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  No datasets found
                </Typography>
              </Box>
            ) : (
              options?.map((option) => (
                <MenuItem
                  key={option.value}
                  value={option.value}
                  onClick={() => handleSelect(option)}
                >
                  {multiple && <Checkbox />}
                  {option.label}
                </MenuItem>
              ))
            )}
          </Box>
        </Box>
      </Popover>
    );
  },
);

DatasetSelectDropDown.displayName = "DatasetSelectDropDown";

DatasetSelectDropDown.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  multiple: PropTypes.bool,
  onSelect: PropTypes.func,
  fetchOptions: PropTypes.func.isRequired,
  searchPlaceholder: PropTypes.string,
  labelText: PropTypes.string,
};

export default DatasetSelectDropDown;
