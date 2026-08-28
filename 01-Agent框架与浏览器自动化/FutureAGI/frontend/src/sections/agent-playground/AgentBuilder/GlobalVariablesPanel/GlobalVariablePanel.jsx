import { Button } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import SvgColor from "src/components/svg-color";
import { useWorkflowRunStoreShallow } from "../../store";
import GlobalVariableDrawer from "./GlobalVariableDrawer";

const BUTTON_MARGIN = 10;

export default function GlobalVariablePanel({
  globalVariablesDrawerOpen,
  setGlobalVariablesDrawerOpen,
}) {
  const isRunning = useWorkflowRunStoreShallow((s) => s.isRunning);

  return (
    <>
      <span
        style={{
          position: "absolute",
          top: BUTTON_MARGIN,
          right: BUTTON_MARGIN,
          transition: "right 0.15s ease-out",
        }}
      >
        <Button
          onClick={() => setGlobalVariablesDrawerOpen(true)}
          disabled={isRunning}
          size="small"
          variant="outlined"
          startIcon={
            <SvgColor
              sx={{
                width: "16px",
                cursor: "pointer",
                color: "text.primary",
              }}
              src="/assets/icons/ic_variables.svg"
            />
          }
        >
          Add input variables
        </Button>
      </span>
      <GlobalVariableDrawer
        open={globalVariablesDrawerOpen}
        onClose={() => setGlobalVariablesDrawerOpen(false)}
      />
    </>
  );
}

GlobalVariablePanel.propTypes = {
  globalVariablesDrawerOpen: PropTypes.bool.isRequired,
  setGlobalVariablesDrawerOpen: PropTypes.func.isRequired,
};
