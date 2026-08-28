import { diffLines, diffWordsWithSpace } from "diff";

/**
 * Compute properly aligned side-by-side diff lines.
 *
 * @param {string} original - The baseline/original prompt text
 * @param {string} optimized - The optimized/new prompt text
 * @returns {{ leftLines: DiffLine[], rightLines: DiffLine[] }}
 *
 * DiffLine shape:
 * {
 *   text: string,           // The line text
 *   type: 'unchanged' | 'added' | 'removed' | 'modified' | 'filler',
 *   lineNumber: number | null,  // null for filler lines
 *   diffParts: Array<{ text: string, status: 'added' | 'removed' | 'default' }> | null
 * }
 */
export function computeAlignedDiff(original, optimized) {
  const lineDiffs = diffLines(original || "", optimized || "");

  const groups = [];
  let i = 0;
  while (i < lineDiffs.length) {
    const part = lineDiffs[i];
    if (part.removed && i + 1 < lineDiffs.length && lineDiffs[i + 1].added) {
      groups.push({ type: "modified", removed: part, added: lineDiffs[i + 1] });
      i += 2;
    } else if (part.added) {
      groups.push({ type: "added", part });
      i += 1;
    } else if (part.removed) {
      groups.push({ type: "removed", part });
      i += 1;
    } else {
      groups.push({ type: "unchanged", part });
      i += 1;
    }
  }

  const leftLines = [];
  const rightLines = [];
  let leftLineNum = 0;
  let rightLineNum = 0;

  for (const group of groups) {
    if (group.type === "unchanged") {
      const lines = splitLines(group.part.value);
      for (const line of lines) {
        leftLineNum += 1;
        rightLineNum += 1;
        leftLines.push({
          text: line,
          type: "unchanged",
          lineNumber: leftLineNum,
          diffParts: null,
        });
        rightLines.push({
          text: line,
          type: "unchanged",
          lineNumber: rightLineNum,
          diffParts: null,
        });
      }
    } else if (group.type === "removed") {
      const lines = splitLines(group.part.value);
      for (const line of lines) {
        leftLineNum += 1;
        leftLines.push({
          text: line,
          type: "removed",
          lineNumber: leftLineNum,
          diffParts: [{ text: line, status: "removed" }],
        });
        rightLines.push({
          text: "",
          type: "filler",
          lineNumber: null,
          diffParts: null,
        });
      }
    } else if (group.type === "added") {
      const lines = splitLines(group.part.value);
      for (const line of lines) {
        rightLineNum += 1;
        leftLines.push({
          text: "",
          type: "filler",
          lineNumber: null,
          diffParts: null,
        });
        rightLines.push({
          text: line,
          type: "added",
          lineNumber: rightLineNum,
          diffParts: [{ text: line, status: "added" }],
        });
      }
    } else if (group.type === "modified") {
      const removedLines = splitLines(group.removed.value);
      const addedLines = splitLines(group.added.value);
      const maxLen = Math.max(removedLines.length, addedLines.length);

      for (let j = 0; j < maxLen; j += 1) {
        const oldLine = removedLines[j];
        const newLine = addedLines[j];

        if (oldLine !== undefined && newLine !== undefined) {
          leftLineNum += 1;
          rightLineNum += 1;
          const wordDiff = diffWordsWithSpace(oldLine, newLine);
          const leftParts = wordDiff
            .filter((p) => !p.added)
            .map((p) => ({
              text: p.value,
              status: p.removed ? "removed" : "default",
            }));
          const rightParts = wordDiff
            .filter((p) => !p.removed)
            .map((p) => ({
              text: p.value,
              status: p.added ? "added" : "default",
            }));

          leftLines.push({
            text: oldLine,
            type: "modified",
            lineNumber: leftLineNum,
            diffParts: leftParts,
          });
          rightLines.push({
            text: newLine,
            type: "modified",
            lineNumber: rightLineNum,
            diffParts: rightParts,
          });
        } else if (oldLine !== undefined) {
          leftLineNum += 1;
          leftLines.push({
            text: oldLine,
            type: "removed",
            lineNumber: leftLineNum,
            diffParts: [{ text: oldLine, status: "removed" }],
          });
          rightLines.push({
            text: "",
            type: "filler",
            lineNumber: null,
            diffParts: null,
          });
        } else {
          rightLineNum += 1;
          leftLines.push({
            text: "",
            type: "filler",
            lineNumber: null,
            diffParts: null,
          });
          rightLines.push({
            text: newLine,
            type: "added",
            lineNumber: rightLineNum,
            diffParts: [{ text: newLine, status: "added" }],
          });
        }
      }
    }
  }

  return { leftLines, rightLines };
}

function splitLines(text) {
  const lines = text.split("\n");
  // diffLines includes trailing newlines in its output, producing empty last element
  if (lines.length > 0 && lines[lines.length - 1] === "") {
    lines.pop();
  }
  return lines;
}
