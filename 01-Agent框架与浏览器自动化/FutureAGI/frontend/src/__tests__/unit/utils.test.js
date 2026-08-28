import { describe, it, expect } from "vitest";

// Example unit tests for utility functions
// These tests should be fast and isolated

describe("Unit: Utility Functions", () => {
  describe("Array helpers", () => {
    it("should handle empty arrays correctly", () => {
      const result = [];
      expect(result).toHaveLength(0);
    });

    it("should process arrays efficiently", () => {
      const input = [1, 2, 3, 4, 5];
      const result = input.map((n) => n * 2);
      expect(result).toEqual([2, 4, 6, 8, 10]);
    });
  });

  describe("String helpers", () => {
    it("should handle string formatting", () => {
      const text = "hello world";
      expect(text.toUpperCase()).toBe("HELLO WORLD");
    });

    it("should validate email format", () => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      expect(emailRegex.test("test@example.com")).toBe(true);
      expect(emailRegex.test("invalid-email")).toBe(false);
    });
  });

  describe("Math helpers", () => {
    it("should calculate percentages correctly", () => {
      const calculatePercentage = (value, total) => (value / total) * 100;
      expect(calculatePercentage(25, 100)).toBe(25);
      expect(calculatePercentage(1, 3)).toBeCloseTo(33.33, 2);
    });

    it("should handle edge cases", () => {
      const safeDivide = (a, b) => (b === 0 ? 0 : a / b);
      expect(safeDivide(10, 2)).toBe(5);
      expect(safeDivide(10, 0)).toBe(0);
    });
  });
});
