import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Collapse from "@mui/material/Collapse";
import Iconify from "src/components/iconify";

function StepIcon({ status }) {
  if (status === "completed") {
    return (
      <Iconify
        icon="mdi:check-circle"
        width={18}
        sx={{ color: "success.main" }}
      />
    );
  }
  if (status === "in_progress") {
    return <CircularProgress size={16} thickness={4} />;
  }
  if (status === "error") {
    return (
      <Iconify
        icon="mdi:alert-circle"
        width={18}
        sx={{ color: "error.main" }}
      />
    );
  }
  return (
    <Iconify
      icon="mdi:radiobox-blank"
      width={18}
      sx={{ color: "text.disabled" }}
    />
  );
}

StepIcon.propTypes = {
  status: PropTypes.string.isRequired,
};

export default function ThoughtsSection({ thoughts, isStreaming }) {
  // Auto-expand when streaming, allow manual toggle when done
  const hasInProgress = thoughts?.some((t) => t.status === "in_progress");
  const [manualToggle, setManualToggle] = useState(null); // null = auto mode

  // Auto-expand during streaming
  useEffect(() => {
    if (hasInProgress || isStreaming) {
      setManualToggle(null); // reset to auto mode during streaming
    }
  }, [hasInProgress, isStreaming]);

  if (!thoughts || thoughts.length === 0) return null;

  const expanded =
    manualToggle !== null ? manualToggle : hasInProgress || isStreaming;

  const completedCount = thoughts.filter(
    (t) => t.status === "completed",
  ).length;
  const totalCount = thoughts.length;
  const statusText =
    hasInProgress || isStreaming
      ? `Thinking... (${completedCount}/${totalCount})`
      : `${completedCount} step${completedCount !== 1 ? "s" : ""} completed`;

  return (
    <Box
      sx={{
        mb: 1.5,
        border: 1,
        borderColor: hasInProgress ? "primary.main" : "divider",
        borderRadius: 1.5,
        overflow: "hidden",
        transition: "border-color 0.2s",
      }}
    >
      {/* Header — always visible */}
      <Box
        onClick={() =>
          setManualToggle((prev) => (prev === null ? !expanded : !prev))
        }
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
          px: 1.5,
          py: 1,
          cursor: "pointer",
          userSelect: "none",
          bgcolor: hasInProgress ? "primary.lighter" : "background.neutral",
          "&:hover": { opacity: 0.85 },
        }}
      >
        {hasInProgress ? (
          <CircularProgress size={14} thickness={5} />
        ) : (
          <Iconify
            icon="mdi:check-circle"
            width={16}
            sx={{ color: "success.main" }}
          />
        )}
        <Typography variant="caption" fontWeight={600} sx={{ flex: 1 }}>
          {statusText}
        </Typography>
        <Iconify
          icon={expanded ? "mdi:chevron-up" : "mdi:chevron-down"}
          width={18}
          sx={{ color: "text.secondary" }}
        />
      </Box>

      {/* Steps timeline — collapsible */}
      <Collapse in={expanded}>
        <Box sx={{ px: 1.5, py: 1 }}>
          {thoughts.map((thought, index) => (
            <Box
              key={thought.step ?? index}
              sx={{
                display: "flex",
                gap: 1,
                mb: index < thoughts.length - 1 ? 0.5 : 0,
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  pt: 0.25,
                }}
              >
                <StepIcon status={thought.status} />
                {index < thoughts.length - 1 && (
                  <Box
                    sx={{
                      width: "1.5px",
                      flex: 1,
                      bgcolor: "divider",
                      mt: 0.25,
                      minHeight: 8,
                    }}
                  />
                )}
              </Box>
              <Box sx={{ pb: 0.75, minWidth: 0 }}>
                <Typography
                  variant="body2"
                  fontWeight={thought.status === "in_progress" ? 600 : 400}
                  sx={{
                    color:
                      thought.status === "pending"
                        ? "text.disabled"
                        : "text.primary",
                  }}
                >
                  {thought.name}
                </Typography>
                {thought.result && (
                  <Typography
                    variant="caption"
                    sx={{
                      color: "text.secondary",
                      display: "block",
                      mt: 0.25,
                    }}
                  >
                    {thought.result}
                  </Typography>
                )}
              </Box>
            </Box>
          ))}
        </Box>
      </Collapse>
    </Box>
  );
}

ThoughtsSection.propTypes = {
  thoughts: PropTypes.arrayOf(
    PropTypes.shape({
      step: PropTypes.number,
      name: PropTypes.string,
      status: PropTypes.string,
      result: PropTypes.string,
    }),
  ),
  isStreaming: PropTypes.bool,
};
