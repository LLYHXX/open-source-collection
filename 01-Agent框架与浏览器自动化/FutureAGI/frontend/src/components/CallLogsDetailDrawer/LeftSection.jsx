import React from "react";
import { Stack } from "@mui/material";
import PropTypes from "prop-types";
import LeftSectionBottom from "./LeftSectionBottom";

const LeftSection = ({ data }) => {
  return (
    <Stack
      gap={2}
      p={2}
      sx={{
        borderRadius: 1,
        border: "1px solid",
        borderColor: "divider",
      }}
      alignItems={"center"}
    >
      <LeftSectionBottom data={data} />
    </Stack>
  );
};

LeftSection.propTypes = {
  data: PropTypes.object.isRequired,
};

export default LeftSection;
