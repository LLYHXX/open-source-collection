export const convertToISO = (dateArray) => {
  return dateArray.map((date) => {
    const d = new Date(date);
    // d.setHours(0, 0, 0, 0); // Set time to 00:00:00.000
    return d.toISOString();
  });
};

export const normalizeTimestamp = (timestamp) => {
  if (!timestamp) return timestamp;

  // Remove common timezone patterns: +00:00, -05:00, Z, etc.
  return timestamp.replace(/([+-]\d{2}:\d{2}|Z)$/, "");
};
