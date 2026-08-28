import { useContext } from "react";
import { GatewayContext } from "./GatewayContext";

export function useGatewayContext() {
  const ctx = useContext(GatewayContext);
  if (!ctx) {
    throw new Error("useGatewayContext must be used within a GatewayProvider");
  }
  return ctx;
}
