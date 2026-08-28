export const getCsatScoreColor = (n) => {
  if (n <= 5) return "red.500";
  if (n <= 7) return "orange.500";
  return "green.500";
};
