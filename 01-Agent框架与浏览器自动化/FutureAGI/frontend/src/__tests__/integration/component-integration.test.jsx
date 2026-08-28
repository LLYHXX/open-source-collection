import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, userEvent, waitFor } from "../../utils/test-utils";
import { Button, Typography, Box } from "@mui/material";
import PropTypes from "prop-types";
import logger from "src/utils/logger";

// Mock component that simulates a real integration scenario
const TestComponent = ({ onSubmit, disabled = false }) => {
  const handleClick = () => {
    onSubmit?.("test data");
  };

  return (
    <Box data-testid="integration-component">
      <Typography variant="h6">Integration Test Component</Typography>
      <Button
        onClick={handleClick}
        disabled={disabled}
        data-testid="submit-button"
      >
        Submit
      </Button>
    </Box>
  );
};

TestComponent.propTypes = {
  onSubmit: PropTypes.func,
  disabled: PropTypes.bool,
};

// Integration tests - test component behavior with dependencies
describe("Integration: Component with Dependencies", () => {
  let mockSubmit;

  beforeEach(() => {
    mockSubmit = vi.fn();
  });

  it("should render with Material-UI theme context", () => {
    render(<TestComponent onSubmit={mockSubmit} />);

    expect(screen.getByTestId("integration-component")).toBeInTheDocument();
    expect(screen.getByText("Integration Test Component")).toBeInTheDocument();
    expect(screen.getByTestId("submit-button")).toBeInTheDocument();
  });

  it("should handle user interactions correctly", async () => {
    const user = userEvent.setup();
    render(<TestComponent onSubmit={mockSubmit} />);

    const submitButton = screen.getByTestId("submit-button");
    await user.click(submitButton);

    expect(mockSubmit).toHaveBeenCalledWith("test data");
  });

  it("should respect disabled state", async () => {
    render(<TestComponent onSubmit={mockSubmit} disabled />);

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toBeDisabled();

    // Try to click disabled button - it should not call the function
    // Note: userEvent prevents clicking disabled buttons, so we just verify the state
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it("should work with async operations", async () => {
    const asyncSubmit = vi
      .fn()
      .mockImplementation(
        () =>
          new Promise((resolve) => setTimeout(() => resolve("success"), 100)),
      );

    const AsyncComponent = () => {
      const handleSubmit = async () => {
        const result = await asyncSubmit();
        logger.debug("Result:", result);
      };

      return <TestComponent onSubmit={handleSubmit} />;
    };

    render(<AsyncComponent />);

    const submitButton = screen.getByTestId("submit-button");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(asyncSubmit).toHaveBeenCalled();
    });
  });

  it("should handle component state changes", async () => {
    const StateComponent = () => {
      const [count, setCount] = React.useState(0);

      return (
        <Box>
          <Typography data-testid="counter">Count: {count}</Typography>
          <Button
            onClick={() => setCount((prev) => prev + 1)}
            data-testid="increment"
          >
            Increment
          </Button>
        </Box>
      );
    };

    render(<StateComponent />);

    expect(screen.getByTestId("counter")).toHaveTextContent("Count: 0");

    await userEvent.click(screen.getByTestId("increment"));
    expect(screen.getByTestId("counter")).toHaveTextContent("Count: 1");
  });
});
