import { describe, it, expect } from "vitest";
import {
  annotationLabelEndpoints,
  annotationLabelKeys,
} from "../annotation-labels";

describe("Annotation Labels API", () => {
  describe("endpoints", () => {
    it("has correct list endpoint", () => {
      expect(annotationLabelEndpoints.list).toBe(
        "/model-hub/annotations-labels/",
      );
    });

    it("has correct create endpoint", () => {
      expect(annotationLabelEndpoints.create).toBe(
        "/model-hub/annotations-labels/",
      );
    });

    it("generates correct detail endpoint", () => {
      expect(annotationLabelEndpoints.detail("abc-123")).toBe(
        "/model-hub/annotations-labels/abc-123/",
      );
    });

    it("generates correct restore endpoint", () => {
      expect(annotationLabelEndpoints.restore("abc-123")).toBe(
        "/model-hub/annotations-labels/abc-123/restore/",
      );
    });
  });

  describe("query keys", () => {
    it("has correct all key", () => {
      expect(annotationLabelKeys.all).toEqual(["annotation-labels"]);
    });

    it("generates list key with filters", () => {
      const filters = { type: "categorical", page: 1 };
      expect(annotationLabelKeys.list(filters)).toEqual([
        "annotation-labels",
        "list",
        filters,
      ]);
    });

    it("generates detail key", () => {
      expect(annotationLabelKeys.detail("abc-123")).toEqual([
        "annotation-labels",
        "detail",
        "abc-123",
      ]);
    });
  });
});
