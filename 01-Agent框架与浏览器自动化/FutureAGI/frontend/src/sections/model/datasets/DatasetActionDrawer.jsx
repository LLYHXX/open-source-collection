import { Drawer, IconButton, styled } from "@mui/material";
import React from "react";

const DrawerHeader = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(0, 1),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
  justifyContent: "flex-start",
}));

const DatasetActionDrawer = () => {
  return (
    <Drawer
      sx={{
        width: "120px",
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: "120px",
        },
      }}
      variant="persistent"
      anchor="right"
      open={true}
    >
      <DrawerHeader>
        <IconButton onClick={() => {}}>t</IconButton>
      </DrawerHeader>
    </Drawer>
  );
};

export default DatasetActionDrawer;
