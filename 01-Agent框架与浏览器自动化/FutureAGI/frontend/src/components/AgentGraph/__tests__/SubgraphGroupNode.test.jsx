import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";

vi.mock("@xyflow/react", () => ({
  // eslint-disable-next-line react/prop-types
  Handle: ({ type, position }) => (
    <div data-testid={`handle-${type}`} data-position={position} />
  ),
  Position: { Top: "top", Bottom: "bottom" },
}));

vi.mock("src/components/svg-color", () => ({
  // eslint-disable-next-line react/prop-types
  default: ({ src }) => <div data-testid="svg-color" data-src={src} />,
}));

import SubgraphGroupNode from "../SubgraphGroupNode";

const theme = createTheme({
  palette: {
    mode: "light",
    blue: {
      200: "#90caf9",
      700: "#1976d2",
    },
    green: {
      50: "#e8f5e9",
      500: "#4caf50",
    },
    red: {
      50: "#ffebee",
      500: "#f44336",
    },
  },
});

const renderNode = (data = {}) =>
  render(
    <ThemeProvider theme={theme}>
      <SubgraphGroupNode
        data={{ label: "Agent 1", frontendNodeType: "agent", ...data }}
      />
    </ThemeProvider>,
  );

describe("SubgraphGroupNode", () => {
  it("renders the label text", () => {
    renderNode({ label: "My Agent" });
    expect(screen.getByText("My Agent")).toBeInTheDocument();
  });

  it("renders target (top) and source (bottom) handles", () => {
    renderNode();
    expect(screen.getByTestId("handle-target")).toBeInTheDocument();
    expect(screen.getByTestId("handle-source")).toBeInTheDocument();
  });

  it("renders handles with correct positions", () => {
    renderNode();
    expect(screen.getByTestId("handle-target")).toHaveAttribute(
      "data-position",
      "top",
    );
    expect(screen.getByTestId("handle-source")).toHaveAttribute(
      "data-position",
      "bottom",
    );
  });

  it("renders SvgColor icon", () => {
    renderNode({ frontendNodeType: "agent" });
    expect(screen.getByTestId("svg-color")).toBeInTheDocument();
  });

  it("renders SvgColor with agent icon src from NODE_TYPE_CONFIG", () => {
    renderNode({ frontendNodeType: "agent" });
    expect(screen.getByTestId("svg-color")).toHaveAttribute(
      "data-src",
      "/assets/icons/navbar/ic_agents.svg",
    );
  });

  it("renders with fallback config for unknown frontendNodeType", () => {
    renderNode({ frontendNodeType: "unknown_type" });
    expect(screen.getByText("Agent 1")).toBeInTheDocument();
    expect(screen.getByTestId("svg-color")).toBeInTheDocument();
  });

  it("renders correctly when selected", () => {
    renderNode({ selected: true, nodeExecution: { status: "success" } });
    expect(screen.getByText("Agent 1")).toBeInTheDocument();
  });

  it("renders correctly with error status", () => {
    renderNode({ nodeExecution: { status: "error" } });
    expect(screen.getByText("Agent 1")).toBeInTheDocument();
  });

  it("renders correctly with no nodeExecution (default status)", () => {
    renderNode();
    expect(screen.getByText("Agent 1")).toBeInTheDocument();
  });

  it("sets handles as non-connectable", () => {
    renderNode();
    const handles = screen.getAllByTestId(/handle-/);
    handles.forEach((h) => {
      expect(h).not.toHaveAttribute("isconnectable", "true");
    });
  });
});
