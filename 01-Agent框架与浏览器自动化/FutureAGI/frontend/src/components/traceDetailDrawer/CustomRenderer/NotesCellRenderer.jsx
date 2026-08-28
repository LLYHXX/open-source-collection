import React from "react";
import CustomTooltip from "src/components/tooltip";

// Notes Cell Renderer
export const NotesCellRenderer = (params) => {
  return (
    <CustomTooltip show={true} title={params.value} placement="top" arrow>
      <div
        style={{
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          width: "100%",
        }}
      >
        {params.value}
      </div>
    </CustomTooltip>
  );
};
