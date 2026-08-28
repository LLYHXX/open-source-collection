import { Drawer, IconButton } from "@mui/material";
import React from "react";
import { useTestRunSdkStoreShallow } from "./state";
import SDkComponentVoiceTestRun from "./SDkComponentVoiceTestRun";
import Iconify from "src/components/iconify";

const NewVoiceSimulationDrawer = () => {
  const { sdkCodeOpen, setSdkCodeOpen } = useTestRunSdkStoreShallow((state) => {
    return {
      sdkCodeOpen: state.sdkCodeOpen,
      setSdkCodeOpen: state.setSdkCodeOpen,
    };
  });
  return (
    <Drawer
      anchor="right"
      open={sdkCodeOpen}
      onClose={() => {
        setSdkCodeOpen(false);
      }}
      PaperProps={{
        sx: {
          height: "100vh",
          position: "fixed",
          zIndex: 9999,
          borderRadius: "10px",
          backgroundColor: "background.paper",
          padding: 2,
        },
      }}
      ModalProps={{
        BackdropProps: {
          style: { backgroundColor: "transparent" },
        },
      }}
    >
      <IconButton
        onClick={() => {
          setSdkCodeOpen(false);
        }}
        sx={{ position: "absolute", top: 2, right: 2 }}
      >
        <Iconify icon="mingcute:close-line" />
      </IconButton>

      <SDkComponentVoiceTestRun />
    </Drawer>
  );
};

export default NewVoiceSimulationDrawer;
