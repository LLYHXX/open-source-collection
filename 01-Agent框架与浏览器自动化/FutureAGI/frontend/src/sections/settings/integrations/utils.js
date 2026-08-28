/**
 * Extract a user-friendly error message from an API error object.
 * Handles the standard { response: { data: { result, message, error } } } shape
 * returned by axios mutation errors.
 */
export function getErrorMessage(error, fallback = "Something went wrong") {
  if (!error) return null;
  const data = error?.response?.data ?? error;
  const msg =
    data?.result ||
    data?.message ||
    data?.error ||
    data?.detail ||
    error?.message;
  return typeof msg === "string" ? msg : fallback;
}

/**
 * Unwrap a standard API response to get the inner result.
 * Handles { data: { result: ... } } or { data: ... } shapes.
 */
export function unwrapResponse(response) {
  const raw = response?.data;
  return raw?.result ?? raw;
}
