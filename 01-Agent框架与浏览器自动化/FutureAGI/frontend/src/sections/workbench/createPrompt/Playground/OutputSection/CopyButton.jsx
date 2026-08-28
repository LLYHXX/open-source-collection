import React from "react";
import { enqueueSnackbar } from "notistack";
import { copyToClipboard } from "src/utils/utils";
import PropTypes from "prop-types";
import { IconButton } from "@mui/material";
import SvgColor from "src/components/svg-color";

const CopyButton = ({ value }) => {
  return (
    <IconButton
      onClick={() => {
        copyToClipboard(value);
        enqueueSnackbar("Copied to clipboard", {
          variant: "success",
        });
      }}
      sx={{
        cursor: "pointer",
      }}
    >
      <SvgColor
        src="/assets/icons/ic_copy.svg"
        alt="Copy"
        sx={{ width: "16px", height: "16px" }}
      />
    </IconButton>
  );
};

CopyButton.propTypes = {
  value: PropTypes.string,
};

export default CopyButton;
