/* eslint-disable react/prop-types */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import Versions from "../Versions";
import { useAgentPlaygroundStore } from "../../store";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
let mockVersionsData = null;
let mockIsLoading = false;
const mockIsFetchingNextPage = false;
const mockFetchNextPage = vi.fn();

vi.mock("src/api/agent-playground/agent-playground", () => ({
  useGetGraphVersions: () => ({
    data: mockVersionsData,
    isLoading: mockIsLoading,
    isFetchingNextPage: mockIsFetchingNextPage,
    fetchNextPage: mockFetchNextPage,
    hasNextPage: false,
  }),
}));

vi.mock("src/hooks/use-scroll-end", () => ({
  useScrollEnd: vi.fn(() => ({ current: null })),
}));

vi.mock("src/components/VersionList/VersionList", () => ({
  default: ({ versions, isLoading }) => (
    <div data-testid="version-list">
      <span data-testid="version-count">{versions?.length ?? 0}</span>
      <span data-testid="is-loading">{String(isLoading)}</span>
      {versions?.map((v) => (
        <div key={v.id} data-testid={`version-${v.id}`}>
          {v.versionNameDisplay} {v.isDraft ? "(draft)" : ""}
        </div>
      ))}
    </div>
  ),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const theme = createTheme();
function renderVersions(props = {}) {
  return render(
    <ThemeProvider theme={theme}>
      <Versions selectedVersion={null} onVersionChange={vi.fn()} {...props} />
    </ThemeProvider>,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("Versions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAgentPlaygroundStore.getState().reset();
    mockVersionsData = null;
    mockIsLoading = false;
  });

  it("renders version list component", () => {
    renderVersions();
    expect(screen.getByTestId("version-list")).toBeInTheDocument();
  });

  it("passes loading state to VersionList", () => {
    mockIsLoading = true;
    renderVersions();
    expect(screen.getByTestId("is-loading")).toHaveTextContent("true");
  });

  it("flattens paginated response and computes isDraft", () => {
    mockVersionsData = {
      pages: [
        {
          data: {
            result: {
              versions: [
                {
                  id: "v1",
                  version_number: 1,
                  createdAt: "2024-01-01",
                  commitMessage: "Initial",
                  status: "draft",
                },
                {
                  id: "v2",
                  version_number: 2,
                  createdAt: "2024-01-02",
                  commitMessage: null,
                  status: "active",
                },
              ],
            },
          },
        },
        {
          data: {
            result: {
              versions: [
                {
                  id: "v3",
                  version_number: 3,
                  createdAt: "2024-01-03",
                  status: "inactive",
                },
              ],
            },
          },
        },
      ],
    };

    renderVersions();

    expect(screen.getByTestId("version-count")).toHaveTextContent("3");
    expect(screen.getByTestId("version-v1")).toHaveTextContent("1 (draft)");
    expect(screen.getByTestId("version-v2")).toHaveTextContent("2");
    expect(screen.getByTestId("version-v3")).toHaveTextContent("3");
  });

  it("returns empty array when no pages", () => {
    mockVersionsData = { pages: [] };
    renderVersions();
    expect(screen.getByTestId("version-count")).toHaveTextContent("0");
  });

  it("handles null data gracefully", () => {
    mockVersionsData = null;
    renderVersions();
    expect(screen.getByTestId("version-count")).toHaveTextContent("0");
  });
});
