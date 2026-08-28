import { Box, IconButton, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React, { useRef } from "react";
import Iconify from "src/components/iconify";
import SvgColor from "src/components/svg-color";
import { getUniqueColorPalette } from "src/utils/utils";

export const CustomCompareColumnHeader = (props) => {
  const { displayName, showColumnMenu, col, hideMenu, head, index } = props;
  const refButton = useRef(null);

  const onMenuClicked = () => {
    showColumnMenu(refButton?.current);
  };

  const iconStyle = {
    color: "text.secondary",
  };

  const renderIcon = () => {
    if (props?.isGrouped) {
      const color = getUniqueColorPalette(index);

      return (
        <Box
          sx={{
            color: color.tagForeground,
            backgroundColor: color.tagBackground,
            borderRadius: "4px",
            height: "24px",
            width: "24px",
            mr: 1,
            ml: -1,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <Typography sx={{ fontSize: "12px", fontWeight: 500 }}>
            {head}
          </Typography>
        </Box>
      );
    } else if (col.originType === "run_prompt") {
      return (
        <SvgColor
          src={`/assets/icons/action_buttons/ic_run_prompt.svg`}
          sx={{ width: 20, height: 20, color: "info.main" }}
        />
      );
    } else if (col.originType === "evaluation") {
      return (
        <Iconify
          icon="material-symbols:check-circle-outline"
          sx={{ color: "info.success" }}
        />
      );
    } else if (
      col.originType === "optimisation" ||
      col.originType === "optimisation_evaluation"
    ) {
      return (
        <SvgColor
          src={`/assets/icons/action_buttons/ic_optimize.svg`}
          sx={{ width: 20, height: 20, color: "primary.main" }}
        />
      );
    } else if (col.originType === "annotation_label") {
      return <Iconify icon="jam:write" sx={iconStyle} />;
    } else if (col.dataType === "text") {
      return <Iconify icon="material-symbols:notes" sx={iconStyle} />;
    } else if (col.dataType === "array") {
      return <Iconify icon="material-symbols:data-array" sx={iconStyle} />;
    } else if (col.dataType === "integer") {
      return <Iconify icon="material-symbols:tag" sx={iconStyle} />;
    } else if (col.dataType === "float") {
      return <Iconify icon="tabler:decimal" sx={iconStyle} />;
    } else if (col.dataType === "boolean") {
      return (
        <Iconify icon="material-symbols:toggle-on-outline" sx={iconStyle} />
      );
    } else if (col.dataType === "datetime") {
      return <Iconify icon="tabler:calendar" sx={iconStyle} />;
    } else if (col.dataType === "json") {
      return <Iconify icon="material-symbols:data-object" sx={iconStyle} />;
    } else if (col.dataType === "image") {
      return (
        <SvgColor
          src={`/assets/icons/action_buttons/ic_image.svg`}
          sx={{ width: 20, height: 20, color: "text.secondary" }}
        />
      );
    } else if (col.dataType === "audio") {
      return (
        <SvgColor
          src={`/assets/icons/action_buttons/ic_audio.svg`}
          sx={{ width: 20, height: 20, color: "text.secondary" }}
        />
      );
    }
  };

  return (
    <Box
      id="bla"
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        width: "100%",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
        {renderIcon()}
        <Typography fontWeight={700} fontSize="13px" color={"text.secondary"}>
          {displayName}
        </Typography>
      </Box>
      {!hideMenu && (
        <IconButton size="small" ref={refButton} onClick={onMenuClicked}>
          <Iconify icon="mdi:dots-vertical" />
        </IconButton>
      )}
    </Box>
  );
};

CustomCompareColumnHeader.propTypes = {
  displayName: PropTypes.string.isRequired,
  showColumnMenu: PropTypes.func,
  col: PropTypes.object,
  hideMenu: PropTypes.bool,
  isGrouped: PropTypes.bool,
  head: PropTypes.string,
  index: PropTypes.number,
};

export default CustomCompareColumnHeader;
