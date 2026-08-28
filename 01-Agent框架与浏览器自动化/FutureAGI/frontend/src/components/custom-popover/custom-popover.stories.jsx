import React from "react";
import CustomPopover from "./custom-popover";

const meta = {
  component: CustomPopover,
  title: "UI Components/CustomPopover",
};

export default meta;

const Template = (args) => {
  const [open, setOpen] = React.useState(null);

  const handleOpen = (event) => {
    setOpen(event.currentTarget);
  };

  const handleClose = () => {
    setOpen(null);
  };

  return (
    <div>
      <button onClick={handleOpen}>Open Popover</button>
      <CustomPopover open={open} onClose={handleClose} {...args}>
        <div
          style={{
            padding: 20,
            width: 200,
            height: 100,
            backgroundColor: "var(--bg-paper)",
          }}
        >
          This is the popover content
        </div>
      </CustomPopover>
    </div>
  );
};

export const Default = Template.bind({});
Default.args = {
  arrow: "top-right",
  hiddenArrow: false,
};

export const HiddenArrow = Template.bind({});
HiddenArrow.args = {
  arrow: "top-right",
  hiddenArrow: true,
};
