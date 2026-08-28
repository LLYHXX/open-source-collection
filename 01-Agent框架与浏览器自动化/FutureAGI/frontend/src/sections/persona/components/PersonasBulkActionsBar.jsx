import { Box, Button, Divider, Tooltip, Typography } from "@mui/material";
import PropTypes from "prop-types";
import Iconify from "src/components/iconify";

const PersonasBulkActionsBar = ({
  selectedCount,
  deletableCount,
  onDelete,
  onCancel,
}) => {
  const hasProtected = selectedCount !== deletableCount;
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 2,
        px: 2,
        py: 0.5,
        borderRadius: "8px",
        border: "1px solid",
        borderColor: "divider",
      }}
    >
      <Typography
        variant="body2"
        fontWeight={600}
        color="primary.main"
        sx={{ pr: 1 }}
      >
        {selectedCount} Selected
      </Typography>

      <Divider orientation="vertical" flexItem />

      <Tooltip
        title={
          deletableCount === 0
            ? "System personas cannot be deleted"
            : hasProtected
              ? `${selectedCount - deletableCount} system persona${selectedCount - deletableCount !== 1 ? "s" : ""} will be skipped`
              : ""
        }
        placement="top"
        arrow
      >
        <span>
          <Button
            size="small"
            color="error"
            disabled={deletableCount === 0}
            startIcon={<Iconify icon="solar:trash-bin-trash-bold" width={16} />}
            onClick={onDelete}
            sx={{ fontSize: "13px", textTransform: "none" }}
          >
            Delete
          </Button>
        </span>
      </Tooltip>

      <Typography
        variant="body2"
        color="text.secondary"
        fontWeight={600}
        sx={{ cursor: "pointer" }}
        onClick={onCancel}
      >
        Cancel
      </Typography>
    </Box>
  );
};

PersonasBulkActionsBar.propTypes = {
  selectedCount: PropTypes.number.isRequired,
  deletableCount: PropTypes.number.isRequired,
  onDelete: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

export default PersonasBulkActionsBar;
