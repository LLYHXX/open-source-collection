import PropTypes from "prop-types";

/**
 * @param {{ type: import("./types").NodeType, className?: string }} props
 */
export const NodeIcon = ({ type, className = "" }) => {
  const iconMap = {
    agent: { emoji: "🔀", variantClass: "node-icon--agent" },
    tool: { emoji: "📦", variantClass: "node-icon--tool" },
    prompt: { emoji: "💬", variantClass: "node-icon--prompt" },
    eval: { emoji: "✅", variantClass: "node-icon--eval" },
  };

  const fallback = { emoji: "•", variantClass: "node-icon--default" };
  const { emoji, variantClass } = iconMap[type] || fallback;

  return (
    <div
      className={["node-icon", variantClass, className]
        .filter(Boolean)
        .join(" ")}
    >
      {emoji}
    </div>
  );
};

NodeIcon.propTypes = {
  type: PropTypes.string.isRequired,
  className: PropTypes.string,
};
