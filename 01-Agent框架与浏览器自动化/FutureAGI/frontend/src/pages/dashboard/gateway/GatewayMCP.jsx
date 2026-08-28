import React from "react";
import { Helmet } from "react-helmet-async";
import MCPManagementSection from "src/sections/gateway/mcp/MCPManagementSection";

const GatewayMCP = () => (
  <>
    <Helmet>
      <title>Gateway MCP Tools | Future AGI</title>
    </Helmet>
    <MCPManagementSection />
  </>
);

export default GatewayMCP;
