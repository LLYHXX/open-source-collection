import { Box, IconButton, Skeleton, styled, Typography } from "@mui/material";
import React from "react";
import Iconify from "src/components/iconify";
import PropTypes from "prop-types";
import CustomSelect from "src/components/custom-select/CustomSelect";
import { ShowComponent } from "src/components/show";
import SelectRunsPopover from "./SelectRunsPopover";
import SelectEvalPopover from "./SelectEvalPopover";

const ExperimentSpecificSelect = styled(CustomSelect)(({ theme }) => ({
  minWidth: "145px",
  "& .MuiOutlinedInput-notchedOutline": {
    borderWidth: "2px",
    borderColor: theme.palette.background.neutral,
  },
  "& .MuiSelect-icon": {
    color: theme.palette.text.primary,
  },
}));

const CompareExperimentRightSection = ({
  onClose,
  selectedRuns,
  setSelectedRuns,
  isLoading,
  evalList,
  selectedEvals,
  setSelectedEvals,
}) => {
  return (
    <Box sx={{ display: "flex", gap: "8px", alignItems: "center" }}>
      <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
        <ExperimentSpecificSelect
          size="small"
          label=""
          popoverComponent={(props) => (
            <SelectRunsPopover
              {...props}
              selectedRuns={selectedRuns}
              setSelectedRuns={setSelectedRuns}
            />
          )}
          fullWidth
          multiple
          value={selectedRuns}
          renderValue={(value) => (
            <Typography
              color="text.primary"
              fontSize="14px"
              lineHeight={"22px"}
              fontWeight={400}
            >
              Selected Runs ({value.length})
            </Typography>
          )}
        />
        <ShowComponent condition={isLoading}>
          <Skeleton
            variant="rectangular"
            width={150}
            height={37}
            sx={{ borderRadius: "8px" }}
          />
        </ShowComponent>
        <ShowComponent condition={!isLoading}>
          <ExperimentSpecificSelect
            size="small"
            label=""
            popoverComponent={(props) => (
              <SelectEvalPopover
                {...props}
                evalList={evalList}
                selectedEvals={selectedEvals}
                setSelectedEvals={setSelectedEvals}
              />
            )}
            multiple
            value={selectedEvals}
            renderValue={(value) => (
              <Typography
                color="text.primary"
                fontSize="14px"
                lineHeight={"22px"}
                fontWeight={400}
              >
                Selected Evals ({value.length})
              </Typography>
            )}
            fullWidth
          />
        </ShowComponent>
      </Box>
      {/* <Box sx={{ display: "flex", gap: 1, alignItems: "center", height: "38px" }}>
        <OutlinedButton
          variant="outlined"
          startIcon={
            <Iconify icon="oui:apm-trace" sx={{ color: "text.disabled", width: "14px", height: "14px" }} />
          }
          onClick={() => {
            setIsTraceOpen((v) => !v);
            if (!isTraceOpen) setIsAnnotateOpen(false);
          }}
          sx={{ padding: "5px 24px", color: "text.primary", fontWeight: "400", fontSize: "14px", backgroundColor: isTraceOpen ? "divider" : "" }}
        >
          Trace
        </OutlinedButton>
        <OutlinedButton
          variant="outlined"
          startIcon={<Iconify icon="line-md:star" sx={{ color: "text.disabled", width: "16px", height: "16px" }} />}
          onClick={() => {
            setIsAnnotateOpen((v) => !v);
            if (!isAnnotateOpen) setIsTraceOpen(false);
          }}
          sx={{ padding: "5px 24px", color: "text.primary", fontWeight: "400", fontSize: "14px", backgroundColor: isAnnotateOpen ? "divider" : "" }}
        >
          Annotate
        </OutlinedButton>
      </Box> */}
      <IconButton onClick={onClose} size="small" sx={{ padding: "0px" }}>
        <Iconify icon="akar-icons:cross" color="text.primary" />
      </IconButton>
    </Box>
  );
};

CompareExperimentRightSection.propTypes = {
  onClose: PropTypes.func,
  selectedRuns: PropTypes.array,
  setSelectedRuns: PropTypes.func,
  isLoading: PropTypes.bool,
  evalList: PropTypes.array,
  selectedEvals: PropTypes.array,
  setSelectedEvals: PropTypes.func,
};

export default CompareExperimentRightSection;
