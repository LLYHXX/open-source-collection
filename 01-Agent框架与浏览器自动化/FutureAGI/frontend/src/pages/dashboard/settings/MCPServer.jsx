import { Helmet } from "react-helmet-async";
import MCPSetupPage from "src/sections/settings/mcp-server/MCPSetupPage";

export default function MCPServer() {
  return (
    <>
      <Helmet>
        <title>MCP Server | FutureAGI</title>
      </Helmet>
      <MCPSetupPage />
    </>
  );
}
