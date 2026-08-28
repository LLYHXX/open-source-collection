import { Alert, AlertTitle, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import PropTypes from "prop-types";
import SvgColor from "../svg-color/svg-color";

// REPLACE WITH RELEVANT ICONS
const variantConfig = {
  info: {
    icon: <SvgColor src="/assets/icons/ic_info.svg" />,
    getSx: (theme) => ({
      backgroundColor: alpha(theme.palette.info.main, 0.1),
      color: "info.main",
      "& .MuiAlert-icon > span": {
        color: "info.main",
      },
    }),
  },
  success: {
    icon: <SvgColor src="/assets/icons/ic_info.svg" />,
    getSx: (theme) => ({
      backgroundColor: alpha(theme.palette.success.main, 0.1),
      color: "success.main",
      "& .MuiAlert-icon > span": {
        color: "success.main",
      },
    }),
  },
  warning: {
    icon: <SvgColor src="/assets/icons/ic_critical.svg" />,
    getSx: (theme) => ({
      backgroundColor: alpha(theme.palette.warning.main, 0.05),
      color: "text.primary",
      "& .MuiAlert-icon span": {
        bgcolor: "warning.main",
      },
    }),
  },
  error: {
    icon: <SvgColor src="/assets/icons/ic_info.svg" />,
    getSx: (theme) => ({
      backgroundColor: alpha(theme.palette.error.main, 0.1),
      borderColor: "error.main",
      color: "error.main",
      "& .MuiAlert-icon": {
        color: "error.main",
      },
    }),
  },
};

const ghostConfig = {
  info: {
    icon: <SvgColor src="/assets/icons/ic_info.svg" />,
    getSx: () => ({
      backgroundColor: "transparent",
      color: "text.primary",
      "& .MuiAlert-icon > span": {
        color: "info.main",
      },
      padding: 0,
    }),
  },
  success: {
    icon: <SvgColor src="/assets/icons/ic_info.svg" />,
    getSx: () => ({
      backgroundColor: "transparent",
      color: "text.primary",
      "& .MuiAlert-icon > span": {
        color: "success.main",
      },
      padding: 0,
    }),
  },
  warning: {
    icon: <SvgColor src="/assets/icons/ic_critical.svg" />,
    getSx: () => ({
      backgroundColor: "transparent",
      color: "text.primary",
      "& .MuiAlert-icon span": {
        bgcolor: "warning.main",
      },
      padding: 0,
    }),
  },
  error: {
    icon: <SvgColor src="/assets/icons/ic_info.svg" />,
    getSx: () => ({
      backgroundColor: "transparent",
      color: "text.primary",
      "& .MuiAlert-icon": {
        color: "error.main",
      },
      padding: 0,
    }),
  },
};

/**
 * @typedef {'info' | 'success' | 'warning' | 'error'} AlertVariant
 * @typedef {'standard' | 'ghost'} AlertType
 */

/**
 * @param {Object} props
 * @param {AlertVariant} [props.variant='info'] - The alert variant (info, success, warning, error)
 * @param {AlertType} [props.type='standard'] - The alert type (standard with background or ghost without background)
 * @param {string} [props.title] - The alert title
 * @param {string} props.message - The alert message
 * @param {Function} [props.onClose] - Callback fired when the close button is clicked
 * @param {Object} [props.sx] - Additional MUI sx styling
 */
export const CustomAlert = ({
  variant = "info",
  type = "standard",
  title,
  message,
  onClose,
  sx,
}) => {
  const config =
    type === "ghost" ? ghostConfig[variant] : variantConfig[variant];

  return (
    <Alert
      severity={variant}
      icon={config.icon}
      onClose={onClose}
      sx={(theme) => ({
        ...config.getSx(theme),
        ...sx,
        display: "flex",
        alignItems: "center",
        borderRadius: "4px !important",
        "& .MuiAlert-message": {
          width: "100%",
        },
        "& .MuiAlert-icon > span": {
          width: 16,
          height: 16,
        },
      })}
    >
      {title && (
        <AlertTitle sx={{ fontWeight: 600, mb: 0.5 }}>{title}</AlertTitle>
      )}
      <Typography
        component="span"
        typography={"s2"}
        color={"text.primary"}
        fontWeight={"fontWeightRegular"}
      >
        {message}
      </Typography>
    </Alert>
  );
};

CustomAlert.propTypes = {
  variant: PropTypes.oneOf(["info", "success", "warning", "error"]),
  type: PropTypes.oneOf(["standard", "ghost"]),
  title: PropTypes.string,
  message: PropTypes.string.isRequired,
  onClose: PropTypes.func,
  sx: PropTypes.object,
};
