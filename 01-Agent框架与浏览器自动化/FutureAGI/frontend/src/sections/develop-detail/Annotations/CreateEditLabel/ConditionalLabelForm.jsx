// @ts-nocheck
import PropTypes from "prop-types";
import React from "react";
import { useWatch } from "react-hook-form";
import TextLabelForm from "./TextLabelForm";
import NumericLabelForm from "./NumericLabelForm";
import StarsLabelForm from "./StarsLabelForm";
import CategoricalLabelForm from "./CategoricalLabelForm";

const ConditionalLabelForm = ({ control }) => {
  const annotationType = useWatch({ control, name: "type" });

  if (annotationType === "text") {
    return <TextLabelForm control={control} />;
  }

  if (annotationType === "numeric") {
    return <NumericLabelForm control={control} />;
  }

  if (annotationType === "star") {
    return <StarsLabelForm />;
  }

  if (annotationType === "categorical") {
    return <CategoricalLabelForm control={control} />;
  }

  return <></>;
};

ConditionalLabelForm.propTypes = {
  control: PropTypes.any,
};

export default ConditionalLabelForm;
