// Computes row-spanning metadata for AG Grid from a sorted list of annotation rows.
// Groups consecutive rows that share the same annotationLabelId into a single visual cell.
// For the first row in each group: sets span = group size and isFirst = true.
// For subsequent rows in the group: sets span = 1 and isFirst = false (cell content hidden).
// Returns a Map keyed by row index so column defs can look up span info in O(1).
export const computeSpanInfo = (data) => {
  const spanMap = new Map();
  let i = 0;
  while (i < data.length) {
    const name = data[i].annotationLabelId;
    let count = 0;
    let j = i;
    while (j < data.length && data[j].annotationLabelId === name) {
      count++;
      j++;
    }
    for (let k = i; k < j; k++) {
      spanMap.set(k, { span: k === i ? count : 1, isFirst: k === i });
    }
    i = j;
  }
  return spanMap;
};
