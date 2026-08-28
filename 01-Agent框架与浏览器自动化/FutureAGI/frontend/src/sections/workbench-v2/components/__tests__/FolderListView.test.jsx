/* eslint-disable react/prop-types */
import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  render,
  screen,
  waitFor,
  within,
  fireEvent,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import FolderListView from "../FolderListView";
import { usePromptStore } from "../../store/usePromptStore";

// ---- Mock react-router ----
vi.mock("react-router", () => ({
  useParams: () => ({ folder: "all" }),
}));

// ---- Mock axios ----
let mockPromptsResponse = null;
vi.mock("src/utils/axios", () => ({
  default: {
    get: vi.fn(() => Promise.resolve(mockPromptsResponse)),
  },
  endpoints: {
    develop: {
      runPrompt: {
        promptExecutions: () => "/model-hub/prompt-executions/",
        promptTemplate: "/model-hub/prompt-base-templates/",
      },
    },
  },
}));

// ---- Mock auth ----
vi.mock("src/auth/hooks", () => ({
  useAuthContext: () => ({ role: "USER" }),
}));

vi.mock("src/utils/rolePermissionMapping", () => ({
  PERMISSIONS: { CREATE: "CREATE" },
  RolePermission: { PROMPTS: { CREATE: { USER: true } } },
}));

// ---- Mock child components ----
vi.mock("../PromptItem", () => ({
  default: ({ name, isLoading }) =>
    isLoading ? (
      <div data-testid="prompt-item-loading" />
    ) : (
      <div data-testid="prompt-item">{name}</div>
    ),
}));

vi.mock("../../../workbench/SelectedPromptTemplateDrawer", () => ({
  SelectedPromptTemplateDrawer: () => null,
}));

vi.mock("src/components/EmptyLayout/EmptyLayout", () => ({
  default: () => <div data-testid="empty-layout" />,
}));

// ---- Helpers ----
const buildResponse = ({ pageSize, totalCount }) => {
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  return {
    data: {
      results: Array.from(
        { length: Math.min(pageSize, totalCount) },
        (_, i) => ({ id: `p-${i}`, name: `Prompt ${i}`, type: "PROMPT" }),
      ),
      count: totalCount,
      total_pages: totalPages,
    },
  };
};

function renderView() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <FolderListView sortConfig={{ field: "updated_at", direction: "desc" }} />
    </QueryClientProvider>,
  );
}

// ---- Tests ----
describe("FolderListView — pagination (TH-4245)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePromptStore.setState({ searchQuery: "", newPromptModal: false });
    mockPromptsResponse = buildResponse({ pageSize: 10, totalCount: 43 });
  });

  it("renders pagination count derived from API total_pages", async () => {
    renderView();

    const pagination = await screen.findByRole("navigation");
    expect(
      within(pagination).getByRole("button", { name: /go to page 5/i }),
    ).toBeInTheDocument();
    expect(
      within(pagination).queryByRole("button", { name: /go to page 6/i }),
    ).not.toBeInTheDocument();
  });

  it("recalculates pagination count when pageLimit changes (no ghost pages)", async () => {
    const axios = (await import("src/utils/axios")).default;
    axios.get.mockImplementation((_url, { params }) =>
      Promise.resolve(
        buildResponse({ pageSize: params.page_size, totalCount: 43 }),
      ),
    );

    renderView();

    const pagination = await screen.findByRole("navigation");
    await waitFor(() =>
      expect(
        within(pagination).getByRole("button", { name: /go to page 5/i }),
      ).toBeInTheDocument(),
    );

    // Change "Result per page" from 10 -> 50
    fireEvent.mouseDown(screen.getByRole("combobox"));
    fireEvent.click(await screen.findByRole("option", { name: "50" }));

    await waitFor(() =>
      expect(
        within(pagination).queryByRole("button", { name: /go to page 5/i }),
      ).not.toBeInTheDocument(),
    );
    expect(
      within(pagination).queryByRole("button", { name: /go to page 2/i }),
    ).not.toBeInTheDocument();
    expect(
      within(pagination).getByRole("button", { name: /page 1/i }),
    ).toBeInTheDocument();
  });
});
