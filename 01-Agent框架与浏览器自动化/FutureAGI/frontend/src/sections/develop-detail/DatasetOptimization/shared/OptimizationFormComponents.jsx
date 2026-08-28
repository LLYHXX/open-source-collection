/**
 * Shared components for optimization forms.
 *
 * Used by:
 * - DatasetOptimizationDrawer (dataset optimization)
 * - RunOptimization (develop-detail optimization)
 */

import React from "react";
import { Box, Typography, Stack, InputAdornment } from "@mui/material";
import PropTypes from "prop-types";
import { ShowComponent } from "src/components/show";
import SvgColor from "src/components/svg-color";
import FormTextFieldV2 from "src/components/FormTextField/FormTextFieldV2";
import { FormSearchSelectFieldControl } from "src/components/FromSearchSelectField";
import { OPTIMIZER_OPTIONS, OPTIMIZER_TYPE } from "../common";

/**
 * Wrapper component for form fields with helper text.
 */
export const FieldWrapper = ({ children, helperText }) => (
  <Box>
    {children}
    {helperText && (
      <Typography
        typography={"s3"}
        fontWeight={"fontWeightMedium"}
        color="text.secondary"
        sx={{ mt: 0.5, display: "block" }}
      >
        {helperText}
      </Typography>
    )}
  </Box>
);

FieldWrapper.propTypes = {
  children: PropTypes.node,
  helperText: PropTypes.string,
};

/**
 * Component to render each optimizer option in the dropdown.
 */
export const OptimizerOptionComponent = ({ model }) => (
  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, py: 0.5 }}>
    <SvgColor
      sx={{ color: "primary.main", width: 24, height: 24 }}
      src={model.icon}
    />
    <Box>
      <Typography variant="body2" fontWeight="fontWeightMedium">
        {model.label}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {model.description}
      </Typography>
    </Box>
  </Box>
);

OptimizerOptionComponent.propTypes = {
  model: PropTypes.shape({
    icon: PropTypes.string,
    label: PropTypes.string,
    description: PropTypes.string,
  }),
};

/**
 * Get the icon for the selected optimizer.
 */
export const getSelectedOptimizerIcon = (optimizerValue) => {
  return (
    OPTIMIZER_OPTIONS.find((e) => e.value === optimizerValue)?.icon ??
    OPTIMIZER_OPTIONS[0].icon
  );
};

/**
 * Optimizer dropdown field with icon adornment.
 */
export const OptimizerSelectField = ({
  control,
  optimizerValue,
  onChange,
  errors,
}) => (
  <FieldWrapper helperText="Choose from our advanced optimizers to refine your prompt.">
    <FormSearchSelectFieldControl
      control={control}
      onChange={onChange}
      options={OPTIMIZER_OPTIONS.map((model) => ({
        ...model,
        component: <OptimizerOptionComponent model={model} />,
      }))}
      InputProps={{
        startAdornment: optimizerValue && (
          <InputAdornment position="start">
            <SvgColor
              sx={{ color: "primary.main", width: 20, height: 20 }}
              src={getSelectedOptimizerIcon(optimizerValue)}
            />
          </InputAdornment>
        ),
      }}
      error={errors?.optimizer_algorithm?.message}
      fieldName="optimizer_algorithm"
      label="Choose Optimizer"
      size="small"
      placeholder="eg: Bayesian Search"
      fullWidth
      required
    />
  </FieldWrapper>
);

OptimizerSelectField.propTypes = {
  control: PropTypes.object.isRequired,
  optimizerValue: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  errors: PropTypes.object,
};

/**
 * Dynamic parameter fields based on selected optimizer type.
 */
export const OptimizerConfigFields = ({
  control,
  optimizerValue,
  onMinMaxChange,
}) => {
  if (!optimizerValue) return null;

  return (
    <Stack
      spacing={2}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        backgroundColor: "background.neutral",
        padding: 2,
        paddingTop: 0,
        borderRadius: 1,
      }}
    >
      <Stack
        sx={{
          position: "sticky",
          top: 0,
          backgroundColor: "background.neutral",
          zIndex: 100,
          paddingTop: 2,
        }}
      >
        <Typography
          typography={"s2"}
          fontWeight={"fontWeightMedium"}
          color={"text.primary"}
        >
          Add Parameters:
        </Typography>
        <Typography
          typography={"s3"}
          color={"text.secondary"}
          fontWeight={"fontWeightRegular"}
        >
          These are the recommended parameters which give a good balance between
          speed and quality of the prompt optimization run
        </Typography>
      </Stack>

      <Stack
        spacing={2}
        sx={{
          border: "1px solid",
          borderColor: "background.neutral",
          borderRadius: 1,
          py: 2,
          px: 1.5,
        }}
      >
        {/* Task Description (all optimizers) */}
        <FormTextFieldV2
          placeholder="(eg: Improve the prompt's response quality)"
          control={control}
          fieldName="optimizer_config.task_description"
          label="Optimization Objective"
          multiline
          minRows={4}
          maxRows={10}
          fullWidth
        />

        {/* Random Search */}
        <ShowComponent
          condition={optimizerValue === OPTIMIZER_TYPE.RANDOM_SEARCH}
        >
          <FieldWrapper helperText="Number of random variations to generate">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.num_variations"
              label="Number Variations"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
        </ShowComponent>

        {/* Bayesian */}
        <ShowComponent condition={optimizerValue === OPTIMIZER_TYPE.BAYESIAN}>
          <FieldWrapper helperText="Minimum number of examples to use">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.min_examples"
              label="Min examples"
              fullWidth
              size="small"
              fieldType="number"
              required
              onChange={onMinMaxChange}
            />
          </FieldWrapper>
          <FieldWrapper helperText="Maximum number of examples to use">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.max_examples"
              label="Max examples"
              fullWidth
              size="small"
              fieldType="number"
              required
              onChange={onMinMaxChange}
            />
          </FieldWrapper>
          <FieldWrapper helperText="Number of optimization trials to run">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.n_trials"
              label="No.of trials"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
        </ShowComponent>

        {/* ProTeGi */}
        <ShowComponent condition={optimizerValue === OPTIMIZER_TYPE.PROTEGI}>
          <FieldWrapper helperText="Number of gradients to compute">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.num_gradients"
              label="Number of gradients"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
          <FieldWrapper helperText="Number of errors to analyze per gradient">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.errors_per_gradient"
              label="Errors per gradient"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
          <FieldWrapper helperText="Number of prompts to generate per gradient">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.prompts_per_gradient"
              label="Prompts per gradient"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
        </ShowComponent>

        {/* PromptWizard */}
        <ShowComponent
          condition={optimizerValue === OPTIMIZER_TYPE.PROMPTWIZARD}
        >
          <FieldWrapper helperText="Number of mutation rounds">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.mutate_rounds"
              label="Mutated Rounds"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
          <FieldWrapper helperText="Number of refinement iterations per round">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.refine_iterations"
              label="Refined Iterations"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
        </ShowComponent>

        {/* Beam Size (ProTeGi & PromptWizard) */}
        <ShowComponent
          condition={
            optimizerValue === OPTIMIZER_TYPE.PROTEGI ||
            optimizerValue === OPTIMIZER_TYPE.PROMPTWIZARD
          }
        >
          <FieldWrapper helperText="Number of candidates to keep at each step">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.beam_size"
              label="Beam size"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
        </ShowComponent>

        {/* Num Rounds (ProTeGi & MetaPrompt) */}
        <ShowComponent
          condition={
            optimizerValue === OPTIMIZER_TYPE.PROTEGI ||
            optimizerValue === OPTIMIZER_TYPE.METAPROMPT
          }
        >
          <FieldWrapper helperText="Number of optimization rounds to run">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.num_rounds"
              label="Number of Rounds"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
        </ShowComponent>

        {/* GEPA */}
        <ShowComponent condition={optimizerValue === OPTIMIZER_TYPE.GEPA}>
          <FieldWrapper helperText="Maximum number of metric evaluations">
            <FormTextFieldV2
              control={control}
              fieldName="optimizer_config.max_metric_calls"
              label="Max Metric Calls"
              fullWidth
              size="small"
              fieldType="number"
              required
            />
          </FieldWrapper>
        </ShowComponent>
      </Stack>
    </Stack>
  );
};

OptimizerConfigFields.propTypes = {
  control: PropTypes.object.isRequired,
  optimizerValue: PropTypes.string,
  onMinMaxChange: PropTypes.func,
};
