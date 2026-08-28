import { useEffect, useMemo, useState } from "react";
import { TreeNode } from "./TreeNode";
import "./TreeNode.css";
import PropTypes from "prop-types";

/**
 * @param {import("./types").TreeNodeData[]} nodes
 * @returns {string[]}
 */
const collectExpandableIds = (nodes) => {
  const ids = [];
  const traverse = (nodeList) => {
    for (const node of nodeList) {
      if (node.children && node.children.length > 0) {
        ids.push(node.id);
        traverse(node.children);
      }
    }
  };
  traverse(nodes);
  return ids;
};

/**
 * @param {{
 *   data: import("./types").TreeNodeData[];
 *   customNodeComponent?: React.ComponentType<any>;
 *   selectedNodeId?: string | null;
 *   onNodeSelect?: (id: string) => void;
 * }} props
 */
export const TreeView = ({
  data,
  customNodeComponent,
  selectedNodeId: externalSelectedId,
  onNodeSelect: externalOnNodeSelect,
}) => {
  const expandableIds = useMemo(() => collectExpandableIds(data), [data]);
  const [internalSelectedId, setInternalSelectedId] = useState(null);
  const [expandedIds, setExpandedIds] = useState(() => new Set(expandableIds));

  // Use external selectedId if provided, otherwise use internal state
  const selectedId =
    externalSelectedId !== undefined ? externalSelectedId : internalSelectedId;
  const onNodeSelect =
    externalOnNodeSelect ||
    ((id) => {
      setInternalSelectedId((prev) => (prev === id ? null : id));
    });

  // Keep expanded state in sync when the data changes (expand all by default).
  useEffect(() => {
    setExpandedIds(new Set(expandableIds));
  }, [expandableIds]);

  const handleToggleExpand = (id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="tree-view">
      {data.map((node, index) => (
        <div key={node.id} className="tree-view__item">
          {/* Vertical line connecting root-level items */}
          {index < data.length - 1 && (
            <div
              className="tree-view__root-connector"
              style={{ top: "26px", height: "100%" }}
            />
          )}
          <TreeNode
            node={node}
            isLast={index === data.length - 1}
            selectedId={selectedId}
            expandedIds={expandedIds}
            onSelect={onNodeSelect}
            onToggleExpand={handleToggleExpand}
            customNodeComponent={customNodeComponent}
          />
        </div>
      ))}
    </div>
  );
};

TreeView.propTypes = {
  data: PropTypes.array.isRequired,
  customNodeComponent: PropTypes.elementType,
  selectedNodeId: PropTypes.string,
  onNodeSelect: PropTypes.func,
};
