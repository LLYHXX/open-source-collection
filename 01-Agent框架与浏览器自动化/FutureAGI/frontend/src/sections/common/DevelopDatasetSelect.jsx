import { MenuItem, Select, styled } from "@mui/material";
import PropTypes from "prop-types";
import React, { useRef, useState } from "react";
import DatasetSelectDropDown from "../develop-detail/DatasetSelectDropDown";
import { useDevelopDatasetList } from "src/api/develop/develop-detail";
import { useNavigate } from "react-router";
import { useSearchParams } from "src/routes/hooks";

const DevelopSelect = styled(Select)(({ theme }) => ({
  "& .MuiSelect-select": {
    paddingTop: 4,
    paddingBottom: 4,
    color: theme.palette.text.primary,
    fontWeight: 500,
  },
}));

const DevelopDatasetSelect = ({ options, value, setValue, ...rest }) => {
  const [selectOpen, setSelectOpen] = useState(false);
  const anchorRef = useRef(null);
  const navigate = useNavigate();
  const [queryParamState] = useSearchParams({
    tab: "",
  });

  return (
    <>
      <DevelopSelect
        size="small"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        open={selectOpen}
        onOpen={() => setSelectOpen(true)}
        onClose={() => setSelectOpen(false)}
        ref={anchorRef}
        MenuProps={{
          PaperProps: {
            style: {
              display: "none",
            },
          },
        }}
        {...rest}
      >
        <MenuItem value={value}>
          {options?.find((o) => o.value === value)?.label}
        </MenuItem>
      </DevelopSelect>
      <DatasetSelectDropDown
        open={selectOpen}
        fetchOptions={useDevelopDatasetList}
        searchPlaceholder="Search Dataset"
        labelText="All Datasets"
        onClose={() => setSelectOpen(false)}
        ref={anchorRef}
        onSelect={(value) => {
          setSelectOpen(false);
          navigate(
            `/dashboard/develop/${value.value}?tab=${queryParamState?.tab || "data"}`,
          );
        }}
      />
    </>
  );
};

DevelopDatasetSelect.propTypes = {
  options: PropTypes.array,
  value: PropTypes.string,
  setValue: PropTypes.func,
};

export default DevelopDatasetSelect;
