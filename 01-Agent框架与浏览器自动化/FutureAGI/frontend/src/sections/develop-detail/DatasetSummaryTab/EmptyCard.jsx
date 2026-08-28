import React from "react";
import { Box, Typography, useTheme } from "@mui/material";
import { LoadingButton } from "@mui/lab";
import PropTypes from "prop-types";
import Iconify from "src/components/iconify";
import { useAuthContext } from "src/auth/hooks";
import { PERMISSIONS, RolePermission } from "src/utils/rolePermissionMapping";

const EmptyCard = ({
  tab,
  setCurrentTab,
  action,
  datasetId,
  icon = "",
  title = "",
  description = "",
}) => {
  const theme = useTheme();
  const handleAddEvaluation = () => {
    setCurrentTab(tab == "annotation" ? "annotations" : "data");
    action();
  };
  const { role } = useAuthContext();

  // Swap to dark variant if available
  const resolvedIcon =
    theme.palette.mode === "dark" && icon
      ? icon.replace(/\.svg$/, "-dark.svg")
      : icon;

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
        flex: 1,
        height: "97%",
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          flexDirection: "column",
          gap: "16px",
          height: "100%",
          textAlign: "center",
          width: "440px",
          margin: "auto",
        }}
      >
        <img src={resolvedIcon} width={"68px"} />
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: "2px",
          }}
        >
          <Typography
            typography="m3"
            fontWeight={"fontWeightMedium"}
            color="text.primary"
          >
            {title}
          </Typography>
          <Typography
            typography="s1"
            color="text.secondary"
            fontWeight={"fontWeightRegular"}
          >
            {description}
          </Typography>
        </Box>
        {!datasetId && (
          <LoadingButton
            fullWidth
            variant="contained"
            color="primary"
            type="submit"
            onClick={handleAddEvaluation}
            sx={{ width: "max-content" }}
            disabled={!RolePermission.DATASETS[PERMISSIONS.UPDATE][role]}
          >
            <Typography
              typography="s2"
              fontWeight={"fontWeightSemiBold"}
              sx={{ display: "flex", gap: 1 }}
            >
              {/* @ts-ignore */}
              <Iconify icon="mdi:plus" width="16px" height="16px" />
              Add {tab}
            </Typography>
          </LoadingButton>
        )}
      </Box>
    </Box>
  );
};

EmptyCard.propTypes = {
  datasetId: PropTypes.any,
  tab: PropTypes.string,
  setCurrentTab: PropTypes.func.isRequired,
  action: PropTypes.func,
  icon: PropTypes.string,
  title: PropTypes.string,
  description: PropTypes.string,
};
export default EmptyCard;
