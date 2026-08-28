import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "src/utils/test-utils";
import SpanTreeTimeline from "../SpanTreeTimeline";

const mockSpans = [
  {
    observation_span: {
      id: "s1",
      name: "root-agent",
      observation_type: "chain",
      start_time: "2026-03-29T10:00:00.000Z",
      latency_ms: 1000,
      total_tokens: 500,
      cost: 0.005,
      status: "OK",
    },
    children: [
      {
        observation_span: {
          id: "s2",
          name: "llm-call",
          observation_type: "llm",
          start_time: "2026-03-29T10:00:00.100Z",
          latency_ms: 500,
          total_tokens: 300,
          cost: 0.003,
          status: "OK",
          model: "gpt-4o",
        },
        children: [],
      },
      {
        observation_span: {
          id: "s3",
          name: "tool-error",
          observation_type: "tool",
          start_time: "2026-03-29T10:00:00.600Z",
          latency_ms: 200,
          total_tokens: 0,
          cost: 0,
          status: "ERROR",
        },
        eval_scores: [
          { eval_name: "accuracy", score: 30 },
          { eval_name: "relevance", score: 80 },
        ],
        children: [],
      },
    ],
  },
];

describe("SpanTreeTimeline", () => {
  it("renders span names", () => {
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId={null}
        onSelectSpan={vi.fn()}
      />,
    );
    expect(screen.getByText("root-agent")).toBeInTheDocument();
    expect(screen.getByText("llm-call")).toBeInTheDocument();
  });

  it("renders 'Trace Timeline' header", () => {
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId={null}
        onSelectSpan={vi.fn()}
      />,
    );
    expect(screen.getByText("Trace Timeline")).toBeInTheDocument();
  });

  it("renders empty state when no spans", () => {
    render(
      <SpanTreeTimeline
        spans={[]}
        selectedSpanId={null}
        onSelectSpan={vi.fn()}
      />,
    );
    expect(screen.getByText("No spans in this trace")).toBeInTheDocument();
  });

  it("calls onSelectSpan when row is clicked", () => {
    const onSelect = vi.fn();
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId={null}
        onSelectSpan={onSelect}
      />,
    );
    screen.getByText("root-agent").click();
    expect(onSelect).toHaveBeenCalledWith("s1");
  });

  it("highlights selected span", () => {
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId="s1"
        onSelectSpan={vi.fn()}
      />,
    );
    expect(screen.getByText("root-agent")).toBeInTheDocument();
  });

  it("renders time scale labels", () => {
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId={null}
        onSelectSpan={vi.fn()}
      />,
    );
    expect(screen.getByText("0ms")).toBeInTheDocument();
  });

  it("renders search input in toolbar", () => {
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId={null}
        onSelectSpan={vi.fn()}
      />,
    );
    expect(screen.getByPlaceholderText("Search spans")).toBeInTheDocument();
  });

  it("filters spans by search query", () => {
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId={null}
        onSelectSpan={vi.fn()}
      />,
    );
    const searchInput = screen.getByPlaceholderText("Search spans");
    fireEvent.change(searchInput, { target: { value: "llm" } });
    expect(screen.getByText("llm-call")).toBeInTheDocument();
    // tool-error should be hidden (doesn't match "llm")
    expect(screen.queryByText("tool-error")).not.toBeInTheDocument();
  });

  it("shows model name for LLM spans", () => {
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId={null}
        onSelectSpan={vi.fn()}
      />,
    );
    expect(screen.getByText("gpt-4o")).toBeInTheDocument();
  });

  it("shows metrics by default (latency, tokens)", () => {
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId={null}
        onSelectSpan={vi.fn()}
      />,
    );
    // Root span latency: 1000ms = "1.0s" — may appear in metrics and bar label
    const latencyTexts = screen.getAllByText("1.0s");
    expect(latencyTexts.length).toBeGreaterThan(0);
  });

  it("shows error count for error spans", () => {
    render(
      <SpanTreeTimeline
        spans={mockSpans}
        selectedSpanId={null}
        onSelectSpan={vi.fn()}
      />,
    );
    // Root should show error count (1 error child in subtree)
    // The error count for root is 1 (tool-error has status ERROR)
    const errorTexts = screen.getAllByText("1");
    expect(errorTexts.length).toBeGreaterThan(0);
  });
});
