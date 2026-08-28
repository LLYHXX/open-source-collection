import React from "react";
import { Box, Checkbox } from "@mui/material";
import CustomTooltip from "src/components/tooltip";
import RenderMeta from "../RenderMeta";
import GenerateDiffText from "../../GenerateDiffText";
import { commonPropTypes, tooltipSlotProp } from "./cellRendererHelper";

const BooleanCellRenderer = ({
  value,
  valueReason,
  formattedValueReason,
  originType,
  metadata,
  valueInfos,
}) => {
  const isValueTypeArray = Array.isArray(value);
  return (
    <CustomTooltip
      show={Boolean(valueReason?.length)}
      title={formattedValueReason()}
      enterDelay={500}
      enterNextDelay={500}
      leaveDelay={100}
      arrow
      slotProps={tooltipSlotProp}
    >
      {isValueTypeArray ? (
        <GenerateDiffText cellText={value} />
      ) : (
        value && (
          <Box sx={{ display: "flex", justifyContent: "center" }}>
            <Checkbox
              checked={value === "true" || value === "Passed" || value === true}
              disableRipple
            />
            <RenderMeta
              originType={originType}
              meta={metadata}
              valuesInfo={valueInfos}
            />
          </Box>
        )
      )}
    </CustomTooltip>
  );
};

BooleanCellRenderer.propTypes = {
  ...commonPropTypes,
};

export default BooleanCellRenderer;
