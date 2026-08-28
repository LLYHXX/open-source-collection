import { Drawer } from "@mui/material";
import React from "react";
import EvalDrawerSection from "./EvalSection";
import { useTestDetailSideDrawerStoreShallow } from "../states";

const EvalSectionDetailDrawer = () => {
  const { evalView, setEvalView } = useTestDetailSideDrawerStoreShallow(
    (s) => ({ evalView: s.evalView, setEvalView: s.setEvalView }),
  );
  return (
    <Drawer
      open={!!evalView}
      onClose={() => setEvalView(null)}
      anchor="right"
      PaperProps={{
        sx: {
          height: "100vh",
          position: "fixed",
          zIndex: 10,
          boxShadow: "-10px 0px 100px #00000035",
          borderRadius: "0px !important",
          backgroundColor: "background.paper",
          display: "flex",
        },
      }}
      ModalProps={{
        BackdropProps: {
          style: {
            backgroundColor: "transparent",
            borderRadius: "0px !important",
          },
        },
      }}
    >
      <EvalDrawerSection />
    </Drawer>
  );
};

export default EvalSectionDetailDrawer;
