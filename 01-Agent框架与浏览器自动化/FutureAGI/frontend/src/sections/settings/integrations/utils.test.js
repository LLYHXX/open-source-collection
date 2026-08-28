import { describe, expect, it } from "vitest";

import { getErrorMessage } from "./utils";

describe("getErrorMessage", () => {
  it("returns a human-readable detail from top-level errors", () => {
    expect(
      getErrorMessage(
        { detail: "Webhook URL must start with https://" },
        "Failed to create webhook",
      ),
    ).toBe("Webhook URL must start with https://");
  });

  it("falls back when the extracted message is an object", () => {
    expect(
      getErrorMessage(
        { response: { data: { message: { url: ["Invalid URL"] } } } },
        "Failed to create webhook",
      ),
    ).toBe("Failed to create webhook");
  });
});
