/**
 * Shared types for the lightweight TreeView components.
 *
 * This repo uses `jsconfig.json` with `checkJs: true`, so we keep this in JS
 * and expose JSDoc typedefs for editor/typechecking support.
 */

/**
 * @typedef {"agent" | "tool" | "prompt" | "eval"} NodeType
 */

/**
 * @typedef {Object} TreeNodeData
 * @property {string} id
 * @property {NodeType} type
 * @property {string} name
 * @property {number} duration
 * @property {number} tokens
 * @property {number} cost
 * @property {TreeNodeData[]=} children
 */

// Optional helper export for consumers that want a list of supported types.
export const NODE_TYPES = ["agent", "tool", "prompt", "eval"];
