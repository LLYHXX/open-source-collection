import React from "react";
import { Box, Typography } from "@mui/material";
import { LoadingButton } from "@mui/lab";
import PropTypes from "prop-types";
import Iconify from "src/components/iconify";
import logger from "src/utils/logger";

const EmptyCard = ({
  tab,
  setCurrentTab,
  onRunEvaluation,
  onRunPrompt,
  datasetId,
}) => {
  const handleAddEvaluation = () => {
    setCurrentTab("data");
    if (tab === "Evaluations") {
      logger.debug("onRunEvaluation");
      onRunEvaluation();
    } else {
      onRunPrompt();
    }
  };

  return (
    <>
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          flexDirection: "column",
          gap: "28px",
          height: "100%",
          textAlign: "center",
          width: "602px",
          margin: "auto",
        }}
      >
        <img
          src={"/assets/illustrations/no-dataset-added.svg"}
          width={"140px"}
        />
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          <Typography
            variant="s1"
            fontWeight={"fontWeightSemiBold"}
            color="text.primary"
          >
            {tab === "Evaluations"
              ? "No evaluation has been added to this dataset"
              : " No prompt template has been added to this dataset "}
          </Typography>
          <Typography
            variant="s1"
            color="text.secondary"
            fontWeight={"fontWeightRegular"}
          >
            {tab === "Evaluations"
              ? "To view evaluation summary, Apply evaluations to your dataset"
              : " To view prompt summary, Add prompts to your dataset "}
          </Typography>
        </Box>
        {!datasetId && (
          <LoadingButton
            fullWidth
            size="small"
            variant="contained"
            color="primary"
            type="submit"
            onClick={() => handleAddEvaluation()}
            sx={{ width: "max-content" }}
          >
            <Typography
              variant="s2"
              fontWeight={"fontWeightSemiBold"}
              sx={{ display: "flex", gap: 1 }}
            >
              <Iconify icon="mdi:plus" width="16px" height="16px" />
              Add {tab}
            </Typography>
          </LoadingButton>
        )}
      </Box>
    </>
  );
};

EmptyCard.propTypes = {
  datasetId: PropTypes.any,
  dataSet: PropTypes.string,
  tab: PropTypes.string,
  setCurrentTab: PropTypes.func.isRequired,
  onRunEvaluation: PropTypes.func,
  onRunPrompt: PropTypes.func,
};
export default EmptyCard;
