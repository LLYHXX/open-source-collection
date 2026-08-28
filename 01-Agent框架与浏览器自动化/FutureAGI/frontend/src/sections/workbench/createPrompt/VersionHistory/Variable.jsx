import { Typography } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const Variable = ({ value }) => {
  return (
    <Typography
      typography="s1_2"
      color={"success.dark"}
      bgcolor={"success.lighter"}
      fontWeight={500}
    >
      {`{{`}
      {value}
      {`}}`}
    </Typography>
  );
};

Variable.propTypes = {
  value: PropTypes.string,
};

export default Variable;
