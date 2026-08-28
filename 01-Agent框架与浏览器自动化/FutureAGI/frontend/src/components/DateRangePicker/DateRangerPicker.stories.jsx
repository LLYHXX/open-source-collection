// import React from 'react';
// import { Box, Button } from '@mui/material';
// import { DateRangerPicker } from './DateRangerPicker';

// const meta = {
//   component: DateRangerPicker,
//   title: 'UI Components/DateRangerPicker',
// };

// export default meta;

// const Template = (args) => {
//   const [anchorEl, setAnchorEl] = React.useState(null);
//   const [open, setOpen] = React.useState(false);
//   const [dateFilter, setDateFilter] = React.useState([null, null]);
//   const [dateOption, setDateOption] = React.useState('');

//   const handleClick = (event) => {
//     setAnchorEl(event.currentTarget);
//     setOpen(true);
//   };

//   const handleClose = () => {
//     setAnchorEl(null);
//     setOpen(false);
//   };

//   return (
//     <Box>
//       <Button variant="contained" onClick={handleClick}>
//         Open Date Range Picker
//       </Button>
//       <DateRangerPicker
//         {...args}
//         open={open}
//         onClose={handleClose}
//         anchorEl={anchorEl}
//         setDateFilter={setDateFilter}
//         setDateOption={setDateOption}
//       />
//       <Box mt={2}>
//         <p>Selected Date Range: {dateFilter[0]} to {dateFilter[1]}</p>
//         <p>Date Option: {dateOption}</p>
//       </Box>
//     </Box>
//   );
// };

// export const Default = Template.bind({});

// Default.args = {
//   // Any default args if needed
// };

import logger from "src/utils/logger";
import { DateRangerPicker } from "./DateRangerPicker";
import React, { useState } from "react";

const meta = {
  component: DateRangerPicker,
  title: "UI Components/DateRangerPicker",
};

export default meta;

const Template = (args) => {
  const [open, setOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <div>
      <button onClick={handleClick}>Open DateRangerPicker</button>
      <DateRangerPicker
        open={open}
        onClose={handleClose}
        anchorEl={anchorEl}
        setDateFilter={args.setDateFilter}
        setDateOption={args.setDateOption}
      />
    </div>
  );
};

export const Default = Template.bind({});

Default.args = {
  setDateFilter: () => logger.debug("Date filter set"),
  setDateOption: () => logger.debug("Date option set"),
};
