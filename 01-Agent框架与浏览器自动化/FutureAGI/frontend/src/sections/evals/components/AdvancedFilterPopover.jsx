import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Popover,
  Typography,
} from "@mui/material";
import PropTypes from "prop-types";
import { useState } from "react";

const EVAL_TYPE_OPTIONS = [
  { value: "llm", label: "LLM" },
  { value: "code", label: "Code" },
  { value: "agent", label: "Agent" },
];

const OUTPUT_TYPE_OPTIONS = [
  { value: "pass_fail", label: "Pass/fail" },
  { value: "percentage", label: "Percentage" },
  { value: "deterministic", label: "Choices" },
];

const AdvancedFilterPopover = ({
  anchorEl,
  open,
  onClose,
  filters,
  onApply,
}) => {
  const [localEvalType, setLocalEvalType] = useState(filters?.eval_type || []);
  const [localOutputType, setLocalOutputType] = useState(
    filters?.output_type || [],
  );

  const handleToggle = (list, setList, value) => {
    setList((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value],
    );
  };

  const handleApply = () => {
    onApply({
      eval_type: localEvalType.length > 0 ? localEvalType : null,
      output_type: localOutputType.length > 0 ? localOutputType : null,
    });
    onClose();
  };

  const handleClear = () => {
    setLocalEvalType([]);
    setLocalOutputType([]);
    onApply({ eval_type: null, output_type: null });
    onClose();
  };

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
      transformOrigin={{ vertical: "top", horizontal: "left" }}
      slotProps={{ paper: { sx: { p: 2, minWidth: 220 } } }}
    >
      <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
        Eval Type
      </Typography>
      <FormGroup sx={{ mb: 2 }}>
        {EVAL_TYPE_OPTIONS.map((opt) => (
          <FormControlLabel
            key={opt.value}
            control={
              <Checkbox
                size="small"
                checked={localEvalType.includes(opt.value)}
                onChange={() =>
                  handleToggle(localEvalType, setLocalEvalType, opt.value)
                }
              />
            }
            label={<Typography variant="body2">{opt.label}</Typography>}
          />
        ))}
      </FormGroup>

      <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
        Output Type
      </Typography>
      <FormGroup sx={{ mb: 2 }}>
        {OUTPUT_TYPE_OPTIONS.map((opt) => (
          <FormControlLabel
            key={opt.value}
            control={
              <Checkbox
                size="small"
                checked={localOutputType.includes(opt.value)}
                onChange={() =>
                  handleToggle(localOutputType, setLocalOutputType, opt.value)
                }
              />
            }
            label={<Typography variant="body2">{opt.label}</Typography>}
          />
        ))}
      </FormGroup>

      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 1 }}>
        <Button
          size="small"
          onClick={handleClear}
          sx={{ textTransform: "none" }}
        >
          Clear
        </Button>
        <Button
          size="small"
          variant="contained"
          onClick={handleApply}
          sx={{ textTransform: "none" }}
        >
          Apply
        </Button>
      </Box>
    </Popover>
  );
};

AdvancedFilterPopover.propTypes = {
  anchorEl: PropTypes.any,
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  filters: PropTypes.object,
  onApply: PropTypes.func.isRequired,
};

export default AdvancedFilterPopover;
