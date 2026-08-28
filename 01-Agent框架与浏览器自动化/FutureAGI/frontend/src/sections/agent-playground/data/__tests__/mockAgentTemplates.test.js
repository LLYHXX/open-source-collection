import { describe, it, expect, vi } from "vitest";
import {
  AGENT_TEMPLATE_CATEGORIES,
  AGENT_TEMPLATES,
  fetchAgentTemplateCategories,
  fetchAgentTemplates,
  fetchAgentTemplateById,
  loadTemplateToBuilder,
} from "../mockAgentTemplates";

// Use real timers for async tests (these are mock API functions with delays)
describe("mockAgentTemplates – data", () => {
  it("exports 6 categories", () => {
    expect(AGENT_TEMPLATE_CATEGORIES).toHaveLength(6);
    expect(AGENT_TEMPLATE_CATEGORIES.map((c) => c.name)).toContain("analytics");
    expect(AGENT_TEMPLATE_CATEGORIES.map((c) => c.name)).toContain("hr");
  });

  it("exports templates array", () => {
    expect(AGENT_TEMPLATES.length).toBeGreaterThanOrEqual(24);
  });

  it("each template has required fields", () => {
    AGENT_TEMPLATES.forEach((t) => {
      expect(t).toHaveProperty("id");
      expect(t).toHaveProperty("name");
      expect(t).toHaveProperty("description");
      expect(t).toHaveProperty("category");
      expect(t).toHaveProperty("config.nodes");
    });
  });
});

describe("fetchAgentTemplateCategories", () => {
  it("returns categories after delay", async () => {
    const result = await fetchAgentTemplateCategories();
    expect(result.data.result).toEqual(AGENT_TEMPLATE_CATEGORIES);
  });
});

describe("fetchAgentTemplates", () => {
  it("returns all templates with no filter", async () => {
    const result = await fetchAgentTemplates({});
    expect(result.data.result.data.length).toBe(AGENT_TEMPLATES.length);
    expect(result.data.result.totalCount).toBe(AGENT_TEMPLATES.length);
  });

  it("filters by category", async () => {
    const result = await fetchAgentTemplates({ category: "analytics" });
    expect(result.data.result.data.length).toBe(4);
    result.data.result.data.forEach((t) => {
      expect(t.category).toBe("analytics");
    });
  });

  it("filters by search query (name match)", async () => {
    const result = await fetchAgentTemplates({ searchQuery: "Data Analyst" });
    expect(result.data.result.data.length).toBeGreaterThan(0);
    expect(result.data.result.data[0].name).toBe("Data Analyst");
  });

  it("filters by search query (description match)", async () => {
    const result = await fetchAgentTemplates({
      searchQuery: "anomaly detection",
    });
    expect(result.data.result.data.length).toBeGreaterThan(0);
  });

  it("applies pagination", async () => {
    const result = await fetchAgentTemplates({ pageNumber: 0, pageSize: 5 });
    expect(result.data.result.data.length).toBe(5);
    expect(result.data.result.totalCount).toBe(AGENT_TEMPLATES.length);
  });

  it("returns empty for non-matching search", async () => {
    const result = await fetchAgentTemplates({
      searchQuery: "zzz-no-match-zzz",
    });
    expect(result.data.result.data.length).toBe(0);
  });

  it("treats 'all' category as no filter", async () => {
    const result = await fetchAgentTemplates({ category: "all" });
    expect(result.data.result.totalCount).toBe(AGENT_TEMPLATES.length);
  });
});

describe("fetchAgentTemplateById", () => {
  it("returns template by ID", async () => {
    const result = await fetchAgentTemplateById("analytics-1");
    expect(result.data.result.name).toBe("Data Analyst");
  });

  it("throws for non-existent template", async () => {
    await expect(fetchAgentTemplateById("nonexistent")).rejects.toThrow(
      "Template not found",
    );
  });
});

describe("loadTemplateToBuilder", () => {
  it("calls progress callback with increasing percentages", async () => {
    const onProgress = vi.fn();
    await loadTemplateToBuilder("analytics-1", onProgress);

    // analytics-1 has 2 nodes → totalSteps = 4 (init + 2 nodes + finalize)
    expect(onProgress).toHaveBeenCalledTimes(4);

    const calls = onProgress.mock.calls;
    // Verify percentages increase
    for (let i = 1; i < calls.length; i++) {
      expect(calls[i][0]).toBeGreaterThan(calls[i - 1][0]);
    }
    // Last call should be 100%
    expect(calls[calls.length - 1][0]).toBe(100);
  });

  it("returns template data with graph", async () => {
    const result = await loadTemplateToBuilder("analytics-1");
    expect(result.data.templateId).toBe("analytics-1");
    expect(result.data.name).toBe("Data Analyst");
    expect(result.data.nodes).toBeDefined();
    expect(result.data.edges).toBeDefined();
  });

  it("throws for non-existent template", async () => {
    await expect(loadTemplateToBuilder("nonexistent")).rejects.toThrow(
      "Template not found",
    );
  });
});
