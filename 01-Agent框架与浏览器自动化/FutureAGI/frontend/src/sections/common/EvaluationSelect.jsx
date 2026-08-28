import { MenuItem, Select, styled } from "@mui/material";
import PropTypes from "prop-types";
import React, { useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import EvalsSelectDropDown from "../evals/EvalDetails/EvalsSelectDropDown";

const DevelopSelect = styled(Select)(({ theme }) => ({
  "& .MuiSelect-select": {
    paddingTop: 4,
    paddingBottom: 4,
    color: theme.palette.text.primary,
    fontWeight: 500,
  },
}));

const EvalDatasetSelect = ({ options, value, setValue, ...rest }) => {
  const [selectOpen, setSelectOpen] = useState(false);
  const anchorRef = useRef(null);
  const [searchText, setSearchText] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const tab = params.get("tab");

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
      <EvalsSelectDropDown
        open={selectOpen}
        onClose={() => setSelectOpen(false)}
        ref={anchorRef}
        setSearchText={setSearchText}
        searchText={searchText}
        onSelect={(value) => {
          setSelectOpen(false);
          setSearchText("");
          navigate(`/dashboard/evaluations/${value.value}?tab=${tab}`);
        }}
      />
    </>
  );
};

EvalDatasetSelect.propTypes = {
  options: PropTypes.array,
  value: PropTypes.string,
  setValue: PropTypes.func,
};

export default EvalDatasetSelect;
