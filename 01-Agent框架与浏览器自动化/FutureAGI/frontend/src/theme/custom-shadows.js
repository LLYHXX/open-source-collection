import { alpha } from "@mui/material/styles";

import {
  grey,
  info,
  error,
  common,
  primary,
  success,
  warning,
  secondary,
} from "./palette";

// ----------------------------------------------------------------------

export function customShadows(mode) {
  const isLight = mode === "light";
  const color = isLight ? grey[500] : common.black;

  // Dark mode: heavier shadows + borders provide depth on dark backgrounds
  const transparent = alpha(color, isLight ? 0.16 : 0.45);

  return {
    z1: `0 1px 2px 0 ${transparent}`,
    z4: `0 4px 8px 0 ${transparent}`,
    z8: `0 8px 16px 0 ${transparent}`,
    z12: `0 12px 24px -4px ${transparent}`,
    z16: `0 16px 32px -4px ${transparent}`,
    z20: `0 20px 40px -4px ${transparent}`,
    z24: `0 24px 48px 0 ${transparent}`,
    //
    card: isLight
      ? `0 0 2px 0 ${alpha(color, 0.2)}, 0 12px 24px -4px ${alpha(color, 0.12)}`
      : `0 0 0px 1px ${alpha(color, 0.5)}, 0 8px 24px -4px ${alpha(color, 0.4)}`,
    dropdown: isLight
      ? `0 0 2px 0 ${alpha(color, 0.24)}, -20px 20px 40px -4px ${alpha(color, 0.24)}`
      : `0 0 0px 1px ${alpha(color, 0.5)}, 0 12px 32px -4px ${alpha(color, 0.5)}`,
    dialog: isLight
      ? `-40px 40px 80px -8px ${alpha(common.black, 0.24)}`
      : `0 0 0px 1px ${alpha(common.white, 0.06)}, 0 24px 64px -8px ${alpha(common.black, 0.7)}`,
    drawer: isLight
      ? `-10px 0px 100px ${alpha(common.black, 0.21)}`
      : `0 0 0px 1px ${alpha(common.white, 0.06)}, -4px 0px 32px ${alpha(common.black, 0.6)}`,
    //
    // In dark mode, primary is monochrome white (#FAFAFA) not purple
    primary: `0 8px 16px 0 ${alpha(isLight ? primary.main : "#FAFAFA", 0.24)}`,
    info: `0 8px 16px 0 ${alpha(info.main, 0.24)}`,
    secondary: `0 8px 16px 0 ${alpha(secondary.main, 0.24)}`,
    success: `0 8px 16px 0 ${alpha(success.main, 0.24)}`,
    warning: `0 8px 16px 0 ${alpha(warning.main, 0.24)}`,
    error: `0 8px 16px 0 ${alpha(error.main, 0.24)}`,
  };
}
