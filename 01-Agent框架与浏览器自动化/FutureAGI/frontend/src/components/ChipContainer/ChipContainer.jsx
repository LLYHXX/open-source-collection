import PropTypes from "prop-types";
import { Box } from "@mui/material";
import { ShowComponent } from "src/components/show/ShowComponent";
import "./chip-container.css";

export default function ChipContainer({
  chips = [],
  idKey = "id",
  labelKey = "label",
  onRemove,
  canRemove,
  canRemoveKey = null,
  reverse = false,
}) {
  const handleDelete = (id) => {
    onRemove(id);
  };

  const isRemovable = (chip) => {
    if (typeof canRemove === "function") {
      return canRemove(chip);
    }
    if (typeof canRemove === "boolean") {
      return canRemove;
    }
    // If canRemoveKey is provided, check that property
    if (canRemoveKey && typeof chip[canRemoveKey] === "boolean") {
      return chip[canRemoveKey];
    }
    return false;
  };

  return (
    <Box className="chip-container">
      <Box className="chip-wrapper">
        {chips.map((chip) => (
          <Box key={chip[idKey]} className="chip-item">
            <span className="chip-label">{chip[labelKey]}</span>
            <ShowComponent
              condition={reverse ? !isRemovable(chip) : isRemovable(chip)}
            >
              <button
                className="chip-delete"
                onClick={() => handleDelete(chip[idKey])}
                aria-label={`Remove ${chip[labelKey]}`}
              >
                ×
              </button>
            </ShowComponent>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

ChipContainer.propTypes = {
  chips: PropTypes.array.isRequired,
  idKey: PropTypes.string.isRequired,
  onRemove: PropTypes.func.isRequired,
  labelKey: PropTypes.string.isRequired,
  canRemove: PropTypes.oneOfType([PropTypes.bool, PropTypes.func]),
  canRemoveKey: PropTypes.string,
  reverse: PropTypes.bool,
};
