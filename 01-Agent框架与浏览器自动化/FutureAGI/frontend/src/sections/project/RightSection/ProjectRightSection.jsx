import { Box, Button, Typography } from "@mui/material";
import React, { useState } from "react";
import Iconify from "src/components/iconify";
import { Events, trackEvent } from "src/utils/Mixpanel";
import PropTypes from "prop-types";

import NewProjectDrawer from "../NewProject/NewProjectDrawer";
import SvgColor from "src/components/svg-color";
import { useAuthContext } from "src/auth/hooks";
import { PERMISSIONS, RolePermission } from "src/utils/rolePermissionMapping";

const ProjectRightSection = ({ isObserve }) => {
  const { role } = useAuthContext();
  const canWrite =
    RolePermission.OBSERVABILITY[PERMISSIONS.CREATE_EDIT_PROJECT][role];
  const [open, setOpen] = useState(false);

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1.5,
      }}
    >
      {/* <DevelopeSearch
        experimentSearch={projectExperimentSearch}
        setExperimentSearch={setProjectExperimentSearch}
        observeSearch={projectObserveSearch}
        setObserveSearch={setProjectObserveSearch}
        onSearchClick={() => {
          trackEvent(Events.searchProjectClicked);
        }}
      /> */}
      <Button
        variant="outlined"
        size="large"
        sx={{
          color: "text.primary",
          borderColor: "divider",
          padding: 1.5,
          fontSize: "14px",
          height: "38px",
        }}
        startIcon={<SvgColor src="/assets/icons/ic_docs_single.svg" />}
        component="a"
        href={
          isObserve
            ? "https://docs.futureagi.com/docs/observe"
            : "https://docs.futureagi.com/docs/prototype/"
        }
        target="_blank"
      >
        View Docs
      </Button>
      {canWrite && (
        <Button
          variant="contained"
          color="primary"
          sx={{
            px: "24px",
            borderRadius: (theme) => theme.spacing(1),
            height: "38px",
          }}
          startIcon={
            <Iconify
              // @ts-ignore
              icon="octicon:plus-24"
              color="background.paper"
              sx={{
                width: "20px",
                height: "20px",
              }}
            />
          }
          onClick={() => {
            setOpen(true);
            trackEvent(Events.newProjectClicked);
          }}
        >
          <Typography
            typography="s1"
            color={"background.paper"}
            fontWeight={"fontWeightSemiBold"}
          >
            {!isObserve ? `Add Prototype` : `Add Project`}
          </Typography>
        </Button>
      )}
      <NewProjectDrawer open={open} onClose={() => setOpen(false)} />
    </Box>
  );
};

ProjectRightSection.propTypes = {
  isObserve: PropTypes.bool,
};

export default ProjectRightSection;
