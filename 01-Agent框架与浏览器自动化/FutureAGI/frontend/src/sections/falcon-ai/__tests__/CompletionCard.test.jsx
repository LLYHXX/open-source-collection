import PropTypes from "prop-types";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "src/utils/test-utils";
import CompletionCard from "../components/CompletionCard";

// Mock Iconify
function MockIconify({ icon, ...props }) {
  return <span data-testid="iconify" data-icon={icon} {...props} />;
}

MockIconify.propTypes = {
  icon: PropTypes.string.isRequired,
};

vi.mock("src/components/iconify", () => ({
  default: MockIconify,
}));

// Mock useRouter
const mockPush = vi.fn();
vi.mock("src/routes/hooks", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
}));

describe("CompletionCard", () => {
  it("returns null when card is null", () => {
    const { container } = render(<CompletionCard card={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null when card is undefined", () => {
    const { container } = render(<CompletionCard />);
    expect(container.firstChild).toBeNull();
  });

  it("renders card title", () => {
    render(
      <CompletionCard
        card={{ title: "Dataset created", status: "completed" }}
      />,
    );
    expect(screen.getByText("Dataset created")).toBeInTheDocument();
  });

  it("renders summary when provided", () => {
    render(
      <CompletionCard card={{ title: "Done", summary: "3 rows added" }} />,
    );
    expect(screen.getByText("3 rows added")).toBeInTheDocument();
  });

  it("does not render summary when absent", () => {
    render(<CompletionCard card={{ title: "Done" }} />);
    expect(screen.queryByText("3 rows added")).not.toBeInTheDocument();
  });

  it("renders action button when action_label and action_url are provided", () => {
    render(
      <CompletionCard
        card={{
          title: "Dataset created",
          action_label: "Go to dataset",
          action_url: "/dashboard/data/123",
        }}
      />,
    );
    const btn = screen.getByRole("button", { name: /go to dataset/i });
    expect(btn).toBeInTheDocument();
  });

  it("does not render action button when action_url is missing", () => {
    render(
      <CompletionCard
        card={{
          title: "Dataset created",
          action_label: "Go to dataset",
        }}
      />,
    );
    expect(
      screen.queryByRole("button", { name: /go to dataset/i }),
    ).not.toBeInTheDocument();
  });

  it("renders action button when action_path is provided instead of action_url", () => {
    render(
      <CompletionCard
        card={{
          title: "Evaluation done",
          action_label: "View results",
          action_path: "/dashboard/evaluations/456",
        }}
      />,
    );
    const btn = screen.getByRole("button", { name: /view results/i });
    expect(btn).toBeInTheDocument();
  });
});
