import { Box, IconButton, InputAdornment, TextField } from "@mui/material";
import PropTypes from "prop-types";
import React, { useState } from "react";
import Iconify from "src/components/iconify";

const SearchField = ({ searchKey, setSearchKey }) => {
  const [showSearch, setShowSearch] = useState(false);

  return (
    <Box>
      {showSearch ? (
        <TextField
          size="small"
          placeholder="Search"
          sx={{ minWidth: "360px" }}
          value={searchKey}
          autoFocus
          onChange={(e) => setSearchKey(e.target.value)}
          onBlur={() => setShowSearch(false)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Iconify
                  onClick={() => setShowSearch(false)}
                  icon="eva:search-fill"
                  sx={{ color: "text.disabled", cursor: "pointer" }}
                />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <Iconify
                  icon="mingcute:close-line"
                  onClick={() => setSearchKey("")}
                  sx={{ color: "text.secondary", cursor: "pointer" }}
                />
              </InputAdornment>
            ),
          }}
        />
      ) : (
        <IconButton
          size="small"
          sx={{ color: "text.secondary" }}
          onClick={() => setShowSearch(true)}
        >
          <Iconify icon="eva:search-fill" sx={{ color: "text.disabled" }} />
        </IconButton>
      )}
    </Box>
  );
};

export default SearchField;

SearchField.propTypes = {
  searchKey: PropTypes.string,
  setSearchKey: PropTypes.func,
};
