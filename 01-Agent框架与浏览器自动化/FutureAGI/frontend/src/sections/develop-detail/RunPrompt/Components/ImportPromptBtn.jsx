import { Button, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import Iconify from "src/components/iconify";
import SvgColor from "src/components/svg-color";

const iconStyles = {
  height: "16px",
  width: "16px",
  color: "primary.main",
};

export default function ImportPromptBtn({ promptImportred, onClick }) {
  return (
    <Button
      onClick={onClick}
      size="small"
      sx={{
        borderRadius: "4px",
        border: "1px solid",
        borderColor: "primary.main",
        px: "16px",
        py: "6px",
      }}
      startIcon={
        promptImportred ? (
          <Iconify icon="line-md:minus" sx={iconStyles} />
        ) : (
          <SvgColor
            sx={iconStyles}
            src={"/assets/icons/navbar/ic_prompt.svg"}
          />
        )
      }
    >
      <Typography
        variant="s2"
        color={"primary.main"}
        fontWeight={"fontWeightSemiBold"}
      >
        {promptImportred ? "Remove Prompt" : "Import prompt"}
      </Typography>
    </Button>
  );
}

ImportPromptBtn.propTypes = {
  promptImportred: PropTypes.bool,
  onClick: PropTypes.func,
};
