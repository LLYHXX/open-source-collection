import React from "react";
import CustomSelect from "./CustomSelect"; // Correct import

const meta = {
  title: "Components/CustomSelect",
  component: CustomSelect,
};

export default meta;

export const Default = {
  args: {
    label: "Select Option",
    popoverComponent: ({ open, onClose, anchorElement }) => (
      <div
        style={{
          display: open ? "block" : "none",
          position: "absolute",
          backgroundColor: "var(--bg-paper)",
          border: "1px solid var(--border-default)",
          padding: "10px",
          top: anchorElement
            ? anchorElement.offsetTop + anchorElement.offsetHeight
            : 0,
          left: anchorElement ? anchorElement.offsetLeft : 0,
        }}
      >
        <div>Popover Content</div>
        <button onClick={onClose}>Close</button>
      </div>
    ),
  },
};
