import PropTypes from "prop-types";
import React from "react";
import { useWatch } from "react-hook-form";

import logger from "./logger";

const { useEffect } = React;

const PrintFormValues = ({ control, logName }) => {
  const values = useWatch({ control });
  useEffect(() => {
    logger.debug(`${logName || "Form Values"}:`, values);
  }, [values, logName]);

  return <></>;
};

PrintFormValues.propTypes = {
  control: PropTypes.object,
  logName: PropTypes.string,
};

export default PrintFormValues;
