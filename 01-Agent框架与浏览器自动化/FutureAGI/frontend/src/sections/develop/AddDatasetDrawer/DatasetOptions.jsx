import { Box, Chip, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import SvgColor from "src/components/svg-color";

// Icons that are multi-colored logos and should stay as <img>
const IMG_ONLY_ICONS = ["hugging_face"];

const DatasetOptions = ({ title, subTitle, onClick, disabled, icons }) => {
  return (
    <Box
      sx={{
        padding: 2,
        gap: 1,
        display: "flex",
        flexDirection: "column",
        borderRadius: 1,
        border: "1px solid",
        borderColor: "divider",
        cursor: "pointer",
        opacity: disabled ? 0.5 : 1,
        "&:hover": {
          backgroundColor: "background.neutral",
        },
      }}
      onClick={onClick}
    >
      <Box sx={{ display: "flex", gap: 2 }}>
        {icons && (
          <Box>
            {IMG_ONLY_ICONS.includes(icons) ? (
              <img
                src={`/icons/datasets/${icons}.svg`}
                alt={icons}
                width={24}
                height={24}
              />
            ) : (
              <SvgColor
                src={`/icons/datasets/${icons}.svg`}
                sx={{ width: 24, height: 24, color: "text.secondary" }}
              />
            )}
          </Box>
        )}
        <Box>
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Typography
              fontWeight={"fontWeightMedium"}
              color="text.primary"
              variant="s1"
            >
              {title}
            </Typography>
            {disabled && (
              <Chip variant="outlined" label="Coming Soon" size="small" />
            )}
          </Box>
          <Typography
            fontWeight={"fontWeightRegular"}
            color="text.secondary"
            variant="s2"
          >
            {subTitle}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

DatasetOptions.propTypes = {
  title: PropTypes.string,
  subTitle: PropTypes.string,
  onClick: PropTypes.func,
  disabled: PropTypes.bool,
  icons: PropTypes.string,
};

export default DatasetOptions;
