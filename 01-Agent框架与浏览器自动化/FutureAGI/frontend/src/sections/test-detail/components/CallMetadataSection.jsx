import { Box } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";
import MetadataItem from "./MetadataItem";

const CallMetadataSection = ({ items = [], sx = {} }) => {
  return (
    <Box
      sx={{
        display: "flex",
        gap: 0.5,
        alignItems: "center",
        flexWrap: "wrap",
        ...sx,
      }}
    >
      {items.map((item, index) => (
        <MetadataItem
          key={item.id || index}
          showDivider={index > 0}
          {...item}
        />
      ))}
    </Box>
  );
};

CallMetadataSection.propTypes = {
  items: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      condition: PropTypes.bool,
      value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      variant: PropTypes.oneOf(["text", "chip"]),
      iconSrc: PropTypes.string,
      sx: PropTypes.object,
      iconSx: PropTypes.object,
    }),
  ),
  sx: PropTypes.object,
};

export default CallMetadataSection;
