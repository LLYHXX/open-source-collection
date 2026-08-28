import {
  Box,
  MenuItem,
  Popover,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo, useState } from "react";
import { useKnowledgeBaseList } from "src/api/knowledge-base/files";
import FormSearchField from "src/components/FormSearchField/FormSearchField";
import { useDebounce } from "src/hooks/use-debounce";

const KnowledgeSelectDropDown = React.forwardRef(
  ({ open, onClose, onSelect }, ref) => {
    const [searchText, setSearchText] = useState("");
    const debouncedSearchText = useDebounce(searchText.trim(), 500);

    const { data: knowledgeBaseList, isLoading: isKnowledgeLoading } =
      useKnowledgeBaseList(debouncedSearchText);

    const knowledgeBaseOptions = useMemo(
      () =>
        knowledgeBaseList?.map(({ id, name }) => ({
          label: name,
          value: id,
        })),
      [knowledgeBaseList],
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
            placeholder="Search Knowledge base"
            size="small"
            searchQuery={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            fullWidth
          />
          <Typography
            sx={{ paddingX: 1, paddingTop: 1, paddingBottom: "6px" }}
            color="text.disabled"
            fontWeight={600}
            fontSize={12}
          >
            All Knowledge base
          </Typography>
          <Box sx={{ maxHeight: "220px", overflowY: "auto" }}>
            {isKnowledgeLoading ? (
              <Stack
                sx={{ my: "4px", px: "4px" }}
                direction={"column"}
                gap={"4px"}
              >
                {Array(10)
                  .fill(0)
                  .map((_, index) => (
                    <Skeleton key={index} variant="text" height={40} />
                  ))}
              </Stack>
            ) : (
              knowledgeBaseOptions?.map((option) => (
                <MenuItem
                  key={option.value}
                  value={option.value}
                  onClick={() => handleSelect(option)}
                >
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

KnowledgeSelectDropDown.displayName = "KnowledgeSelectDropDown";

KnowledgeSelectDropDown.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  multiple: PropTypes.bool,
  onSelect: PropTypes.func,
};

export default KnowledgeSelectDropDown;
