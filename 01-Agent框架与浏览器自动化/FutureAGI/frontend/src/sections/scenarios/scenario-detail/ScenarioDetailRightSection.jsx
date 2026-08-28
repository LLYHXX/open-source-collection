import { Box, Button, Stack } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { ShowComponent } from "src/components/show";
import SvgColor from "src/components/svg-color";
import { useDevelopSelectedRowsStoreShallow } from "src/sections/develop-detail/states";
import ScenarioDetailSelectionView from "./ScenarioDetailSelectionView";
import { useAuthContext } from "src/auth/hooks";
import { PERMISSIONS, RolePermission } from "src/utils/rolePermissionMapping";
const buttonStyles = {
  color: "text.primary",
  border: "1px solid",
  fontSize: "12px",
  fontWeight: 400,
  lineHeight: "18px",
  borderColor: "divider",
  paddingY: 0.5,
  paddingX: 1.5,
};

const ScenarioDetailRightSection = ({
  scenario,
  setAddRowScenarioOpen,
  setColumnScenarioOpen,
}) => {
  const { isSelected } = useDevelopSelectedRowsStoreShallow((s) => ({
    isSelected: s.selectAll || s.toggledNodes.length > 0,
  }));

  const { role } = useAuthContext();

  return (
    <Box>
      <ShowComponent condition={isSelected}>
        <ScenarioDetailSelectionView dataset={scenario?.dataset} />
      </ShowComponent>
      <ShowComponent condition={!isSelected}>
        <Stack sx={{ display: "flex", flexDirection: "row", gap: 1 }}>
          <Button
            size="small"
            startIcon={
              <SvgColor src={`/assets/icons/action_buttons/ic_add_row.svg`} />
            }
            onClick={() => {
              setAddRowScenarioOpen(true);
            }}
            disabled={
              !scenario?.dataset ||
              !RolePermission.SIMULATION_AGENT[PERMISSIONS.CREATE][role]
            }
            sx={buttonStyles}
          >
            Add Row
          </Button>
          <Button
            size="small"
            startIcon={
              <SvgColor
                src={`/assets/icons/action_buttons/ic_add_column.svg`}
              />
            }
            onClick={() => {
              setColumnScenarioOpen(true);
            }}
            disabled={
              !scenario?.dataset ||
              !RolePermission.SIMULATION_AGENT[PERMISSIONS.CREATE][role]
            }
            sx={buttonStyles}
          >
            Add Column
          </Button>
        </Stack>
      </ShowComponent>
    </Box>
  );
};

ScenarioDetailRightSection.propTypes = {
  scenario: PropTypes.object.isRequired,
  setAddRowScenarioOpen: PropTypes.func.isRequired,
  setColumnScenarioOpen: PropTypes.func.isRequired,
};

export default ScenarioDetailRightSection;
