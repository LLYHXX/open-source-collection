/* eslint-disable react/prop-types */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import {
  DateCellRenderer,
  CollaboratorsCellRenderer,
  NameCellRenderer,
  HeaderComponent,
} from "../cellRenderers";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
import { vi } from "vitest";

vi.mock("src/components/svg-color", () => ({
  default: ({ src, ...props }) => (
    <span data-testid="svg-icon" data-src={src} {...props} />
  ),
}));

vi.mock("src/components/tooltip/CustomTooltip", () => ({
  default: ({ children, title }) => (
    <div data-testid="tooltip" title={title}>
      {children}
    </div>
  ),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const theme = createTheme();
function renderWithTheme(component) {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("NameCellRenderer", () => {
  it("renders the name value", () => {
    renderWithTheme(<NameCellRenderer value="My Agent" />);
    expect(screen.getByText("My Agent")).toBeInTheDocument();
  });
});

describe("DateCellRenderer", () => {
  it("returns dash when value is null", () => {
    renderWithTheme(<DateCellRenderer value={null} />);
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("returns dash when value is undefined", () => {
    renderWithTheme(<DateCellRenderer value={undefined} />);
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("formats a valid ISO date", () => {
    // 2024-01-15T14:30:00Z
    renderWithTheme(<DateCellRenderer value="2024-01-15T14:30:00Z" />);
    // date-fns format: "dd-MM-yyyy, h:mm a"
    const text = screen.getByText(/15-01-2024/);
    expect(text).toBeInTheDocument();
  });

  it("returns dash for invalid date string", () => {
    renderWithTheme(<DateCellRenderer value="not-a-date" />);
    // date-fns will return "Invalid Date" or throw; catch returns "-"
    expect(screen.getByText("-")).toBeInTheDocument();
  });
});

describe("CollaboratorsCellRenderer", () => {
  it("returns dash when value is null", () => {
    renderWithTheme(<CollaboratorsCellRenderer value={null} />);
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("returns dash when value is empty array", () => {
    renderWithTheme(<CollaboratorsCellRenderer value={[]} />);
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("renders avatar initials from collaborator names", () => {
    const collaborators = [
      { name: "Alice", email: "alice@example.com" },
      { name: "Bob", email: "bob@example.com" },
    ];

    renderWithTheme(<CollaboratorsCellRenderer value={collaborators} />);

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
  });

  it("renders tooltips with email addresses", () => {
    const collaborators = [{ name: "Alice", email: "alice@example.com" }];

    renderWithTheme(<CollaboratorsCellRenderer value={collaborators} />);

    expect(screen.getByTitle("alice@example.com")).toBeInTheDocument();
  });
});

describe("HeaderComponent", () => {
  it("renders label text", () => {
    renderWithTheme(<HeaderComponent label="Name" />);
    expect(screen.getByText("Name")).toBeInTheDocument();
  });

  it("renders icon when iconSrc provided", () => {
    renderWithTheme(<HeaderComponent label="Date" iconSrc="/icon.svg" />);
    expect(screen.getByTestId("svg-icon")).toBeInTheDocument();
  });

  it("does not render icon when iconSrc is not provided", () => {
    renderWithTheme(<HeaderComponent label="Date" />);
    expect(screen.queryByTestId("svg-icon")).not.toBeInTheDocument();
  });
});
