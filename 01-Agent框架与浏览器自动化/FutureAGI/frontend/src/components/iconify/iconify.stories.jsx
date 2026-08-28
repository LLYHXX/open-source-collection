import Iconify from "./iconify";

const meta = {
  component: Iconify,
  title: "UI Components/Iconify",
};

export default meta;

export const Default = {
  args: {
    icon: "material-symbols:info-outline",
    width: 40,
    sx: {},
  },
};

export const CustomColorIcon = {
  args: {
    icon: "material-symbols:info-outline",
    width: 40,
    sx: {
      color: "primary.main",
    },
  },
};
