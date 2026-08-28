import React from "react";

import { getFileExtension } from "./utils";

const RenderFileIcons = (fileType) => {
  try {
    const iconType = getFileExtension(fileType) || "default";
    const iconPath = `/icons/fileIcons/${iconType}.svg`;

    return (
      <img
        src={iconPath}
        height={22}
        width={22}
        onError={(e) => {
          e.target.onerror = null;
          e.target.src = "/icons/fileIcons/default.svg";
        }}
        alt={`${fileType} file icon`}
      />
    );
  } catch (error) {
    return (
      <img
        src="/icons/fileIcons/default.svg"
        height={22}
        width={22}
        alt="Default file icon"
      />
    );
  }
};

export default RenderFileIcons;
