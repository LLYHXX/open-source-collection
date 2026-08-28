import { Box } from "@mui/material";
import { Outlet, useParams } from "react-router";
import React, { useEffect, useRef, useState } from "react";
import { useSearchParams } from "src/routes/hooks";
import { ShowComponent } from "src/components/show";
import EvalsSelectRow from "./EvalsSelectRow";
import EvaluationBar from "./EvaluationBar";
import { Helmet } from "react-helmet-async";
import EvalsConfigTab from "./EvalsConfig/EvalsConfigTab";
import EvalsLogTab from "./EvalsLog/EvalsLogTab";
import EvaluationProvider from "src/sections/common/EvaluationDrawer/context/EvaluationProvider";
import { EvaluationContext } from "src/sections/common/EvaluationDrawer/context/EvaluationContext";
import PropTypes from "prop-types";
const ContextConsumer = ({
  context,
  setVisibleSectionRef,
  id,
  showTest,
  showAdd,
  runLabel,
  module,
}) => {
  useEffect(() => {
    if (context) {
      const { setModule, setActionButtonConfig, setVisibleSection } = context;
      if (setVisibleSection) {
        setVisibleSectionRef.current = setVisibleSection;
        setModule(module);
      }
      setActionButtonConfig((pre) => ({
        ...pre,
        id,
        showTest,
        showAdd,
        runLabel,
      }));
    }
  }, [module, id]);
  return null;
};

ContextConsumer.propTypes = {
  id: PropTypes.string,
  showTest: PropTypes.bool,
  showAdd: PropTypes.bool,
  runLabel: PropTypes.string,
  handleTest: PropTypes.func,
  handleRun: PropTypes.func,
  context: PropTypes.object,
  module: PropTypes.string,
  setVisibleSectionRef: PropTypes.any,
};

const EvalDetailView = () => {
  const { evalId } = useParams();
  const tabRef = useRef(null);
  const gridApiRef = useRef(null);
  const [rowSelected, setRowSelected] = useState([]);
  const setVisibleSectionRef = useRef(null);
  const [params, setParams] = useSearchParams({
    tab: "logs",
  });
  const currentTab = params.tab;

  const setCurrentTab = (tab) => {
    setRowSelected([]);
    setParams({ tab });
    onSelectionChanged(null);
  };

  useEffect(() => {
    gridApiRef?.current?.api?.deselectAll();
  }, [evalId]);

  const onSelectionChanged = (event) => {
    if (!event) {
      setTimeout(() => {}, 300);
      gridApiRef?.current?.api.deselectAll();
      return;
    }
  };

  return (
    <Box
      sx={{
        backgroundColor: "background.paper",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: "16px",
      }}
    >
      <Helmet>
        <title>Evaluations - {currentTab || "Logs"}</title>
      </Helmet>
      <EvaluationProvider>
        <EvaluationContext.Consumer>
          {(context) => (
            <ContextConsumer
              context={context}
              setVisibleSectionRef={setVisibleSectionRef}
              id={"2063cf96-40fc-4840-b5cd-ce48f06c24ea"}
              showTest={true}
              showAdd={true}
              runLabel={"Run Label"}
              handleTest={() => {}}
              handleRun={() => {}}
            />
          )}
        </EvaluationContext.Consumer>
        <Box sx={{ height: "calc(100% - 150px)" }}>
          <EvalsSelectRow />
          <EvaluationBar
            currentTab={currentTab}
            setCurrentTab={setCurrentTab}
            rowSelected={rowSelected}
            setRowSelected={setRowSelected}
            tabRef={tabRef}
          />

          <Outlet />
          <ShowComponent condition={currentTab === "config"}>
            <EvalsConfigTab />
          </ShowComponent>
          <ShowComponent condition={currentTab === "logs"}>
            <EvalsLogTab />
          </ShowComponent>
          {/* <ShowComponent condition={currentTab === "feedback"}>
            <LogsTabGrid isFeedback />
          </ShowComponent> */}
        </Box>
      </EvaluationProvider>
    </Box>
  );
};

export default EvalDetailView;
