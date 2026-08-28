import { Box, Chip, Stack, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { ShowComponent } from "src/components/show";
import SvgColor from "src/components/svg-color";
const STATUS_MAP = {
  SUCCESS: "success",
  FAILED: "failed",
};
const UserStatusItem = ({ user, status }) => {
  return (
    <Box
      sx={{
        border: "1px solid var(--border-light)",
        borderRadius: 0.5,
        padding: 1,
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          gap: 1,
        }}
      >
        <ShowComponent condition={status === STATUS_MAP.FAILED}>
          <SvgColor
            sx={{ width: "14px", color: "#FB2C36" }}
            src="/assets/icons/ic_critical.svg"
          />
        </ShowComponent>
        <Stack spacing={0.25}>
          <Typography typography={"s1"} fontWeight={"fontWeightRegular"}>
            {user.email}
          </Typography>
          <ShowComponent condition={status === STATUS_MAP.FAILED}>
            <Typography
              typography={"s2"}
              fontWeight={"fontWeightRegular"}
              color="red.500"
            >
              {user.reason}
            </Typography>
          </ShowComponent>
        </Stack>
        <ShowComponent condition={status === STATUS_MAP.SUCCESS}>
          <Chip
            label={"Added"}
            icon={
              <SvgColor
                sx={{ width: 16, color: "green.700" }}
                src="/assets/icons/ic_completed.svg"
              />
            }
            sx={{
              bgcolor: "transparent",
              color: "green.700",
              "& .MuiChip-icon": {
                color: "green.700",
              },
              ":hover": {
                backgroundColor: "transparent",
              },
            }}
          />
        </ShowComponent>
      </Box>
      <ShowComponent condition={status === STATUS_MAP.FAILED}>
        <Chip
          label={"Failed"}
          icon={
            <SvgColor
              sx={{ width: 14, color: "red.700" }}
              src="/assets/icons/ic_critical.svg"
            />
          }
          sx={{
            color: "red.700",
            backgroundColor: "transparent",
            "& .MuiChip-icon": {
              color: "red.700",
            },
            ":hover": {
              backgroundColor: "transparent",
            },
          }}
        />
      </ShowComponent>
      <ShowComponent condition={status === STATUS_MAP.SUCCESS}>
        <Chip
          size="medium"
          label={"Email Sent"}
          icon={
            <SvgColor sx={{ width: 16 }} src="/assets/icons/ic_email.svg" />
          }
          sx={{
            bgcolor: "green.50",
            color: "green.700",
            px: 1,
            "& .MuiChip-icon": {
              color: "green.700",
              borderRadius: "4px",
            },
            ":hover": {
              backgroundColor: "green.50",
            },
          }}
        />
      </ShowComponent>
    </Box>
  );
};

export default UserStatusItem;
UserStatusItem.propTypes = {
  user: PropTypes.object.isRequired,
  status: PropTypes.string.isRequired,
};
