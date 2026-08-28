import { styled } from "@mui/material";
import { ModelOptionSlider as BaseModelOptionSlider } from "src/components/custom-model-options/SliderRow/ModelOptionSlider";

// Re-styled variant with different rail and mark colors for sections/common usage
export const ModelOptionSlider = styled(BaseModelOptionSlider)(({ theme }) => ({
  "& .MuiSlider-rail": {
    backgroundColor: theme.palette.action.hover,
  },
  "& .MuiSlider-mark": {
    backgroundColor: theme?.palette?.black?.o20,
  },
}));
