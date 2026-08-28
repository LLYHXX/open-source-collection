import { Badge, Box, Button } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import SvgColor from "src/components/svg-color";
import { OutlinedButton } from "src/sections/project-detail/ProjectDetailComponents";

const TracesTabRightSection = React.forwardRef(
  (
    { setOpenColumnConfigure, setOpenFilter, filterOpen, isFilterApplied },
    columnConfigureRef,
  ) => {
    return (
      <Box
        sx={{
          display: "flex",
          gap: (theme) => theme.spacing(1.25),
          alignItems: "center",
        }}
      >
        <Button
          sx={{
            fontWeight: "fontWeightRegular",
            color: "text.primary",
            typography: "s1",
          }}
          onClick={() => setOpenFilter((v) => !v)}
          startIcon={
            isFilterApplied ? (
              <Badge
                variant="dot"
                color="error"
                overlap="circular"
                anchorOrigin={{ vertical: "top", horizontal: "right" }}
                sx={{
                  "& .MuiBadge-badge": {
                    top: 1,
                    right: 1,
                  },
                }}
              >
                <SvgColor src={`/assets/icons/action_buttons/ic_filter.svg`} />
              </Badge>
            ) : (
              <SvgColor src={`/assets/icons/action_buttons/ic_filter.svg`} />
            )
          }
        >
          {filterOpen ? "Hide Filter" : "Show Filter"}
        </Button>
        <OutlinedButton
          startIcon={
            <SvgColor src="/assets/icons/action_buttons/ic_column.svg" />
          }
          variant="outlined"
          ref={columnConfigureRef}
          sx={{
            // color: "text.disabled",
            typography: "s1",
            // paddingX:(theme)=>theme.spacing(3),
            // paddingY:(theme)=>theme.spacing(1)
          }}
          onClick={() => setOpenColumnConfigure(true)}
        >
          Columns
        </OutlinedButton>
      </Box>
    );
  },
);

TracesTabRightSection.displayName = "TracesTabRightSection";

TracesTabRightSection.propTypes = {
  setOpenColumnConfigure: PropTypes.func,
  setOpenFilter: PropTypes.func,
  filterOpen: PropTypes.bool,
  isFilterApplied: PropTypes.bool,
};

export default TracesTabRightSection;
