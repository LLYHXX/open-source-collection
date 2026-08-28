import { describe, it, expect } from "vitest";
import {
  NODE_EXECUTION_STATE,
  WORKFLOW_STATE,
  EXECUTION_STATUS,
  mapApiStatusToNodeState,
} from "../workflowExecution";

describe("workflowExecution constants", () => {
  it("exports NODE_EXECUTION_STATE enum", () => {
    expect(NODE_EXECUTION_STATE.IDLE).toBe("idle");
    expect(NODE_EXECUTION_STATE.RUNNING).toBe("running");
    expect(NODE_EXECUTION_STATE.COMPLETED).toBe("completed");
    expect(NODE_EXECUTION_STATE.ERROR).toBe("error");
  });

  it("exports WORKFLOW_STATE enum", () => {
    expect(WORKFLOW_STATE.IDLE).toBe("idle");
    expect(WORKFLOW_STATE.COMPLETED).toBe("completed");
  });

  it("exports EXECUTION_STATUS enum", () => {
    expect(EXECUTION_STATUS.PENDING).toBe("pending");
    expect(EXECUTION_STATUS.SUCCESS).toBe("success");
    expect(EXECUTION_STATUS.FAILED).toBe("failed");
  });
});

describe("mapApiStatusToNodeState", () => {
  it("maps success to COMPLETED", () => {
    expect(mapApiStatusToNodeState("success")).toBe(
      NODE_EXECUTION_STATE.COMPLETED,
    );
  });

  it("maps failed to ERROR", () => {
    expect(mapApiStatusToNodeState("failed")).toBe(NODE_EXECUTION_STATE.ERROR);
  });

  it("maps error to ERROR", () => {
    expect(mapApiStatusToNodeState("error")).toBe(NODE_EXECUTION_STATE.ERROR);
  });

  it("maps running to RUNNING", () => {
    expect(mapApiStatusToNodeState("running")).toBe(
      NODE_EXECUTION_STATE.RUNNING,
    );
  });

  it("returns null for unrecognized status", () => {
    expect(mapApiStatusToNodeState("unknown")).toBeNull();
  });
});
