import React from "react";
import { Helmet } from "react-helmet-async";
import CallLogsView from "src/sections/test/CallLogs/CallLogsView";

const CallLogs = () => {
  return (
    <>
      <Helmet>
        <title>Call Logs</title>
      </Helmet>
      <CallLogsView />
    </>
  );
};

export default CallLogs;
