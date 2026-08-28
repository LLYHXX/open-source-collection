import React from "react";
import PropTypes from "prop-types";
import { FormProvider as Form } from "react-hook-form";

// ----------------------------------------------------------------------

export default function FormProvider({ children, onSubmit, methods, style }) {
  return (
    <Form {...methods}>
      <form style={style} onSubmit={onSubmit}>
        {children}
      </form>
    </Form>
  );
}

FormProvider.propTypes = {
  children: PropTypes.node,
  methods: PropTypes.object,
  onSubmit: PropTypes.func,
  style: PropTypes.object,
};
