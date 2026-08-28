import React from "react";
import PropTypes from "prop-types";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import { alpha, useTheme } from "@mui/material/styles";
import Iconify from "src/components/iconify";

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(contentType) {
  if (!contentType) return "mdi:file-outline";
  if (contentType.startsWith("image/")) return "mdi:file-image-outline";
  if (contentType === "application/pdf") return "mdi:file-pdf-box";
  if (contentType === "application/json") return "mdi:code-json";
  if (contentType.includes("spreadsheet") || contentType === "text/csv")
    return "mdi:file-table-outline";
  if (contentType.includes("wordprocessing")) return "mdi:file-word-outline";
  if (contentType === "text/html") return "mdi:language-html5";
  if (contentType === "text/markdown") return "mdi:language-markdown-outline";
  return "mdi:file-document-outline";
}

export default function AttachedFileChip({ file, onRemove, readOnly }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";

  const handleClick = () => {
    if (file.url) {
      window.open(file.url, "_blank", "noopener,noreferrer");
    }
  };

  const truncatedName =
    file.name && file.name.length > 28
      ? `${file.name.slice(0, 24)}...${file.name.slice(file.name.lastIndexOf("."))}`
      : file.name;

  return (
    <Box
      onClick={handleClick}
      sx={{
        display: "inline-flex",
        alignItems: "center",
        gap: 0.75,
        px: 1.25,
        py: 0.5,
        borderRadius: "10px",
        bgcolor: isDark
          ? alpha(theme.palette.common.white, 0.06)
          : alpha(theme.palette.common.black, 0.04),
        border: "1px solid",
        borderColor: isDark
          ? alpha(theme.palette.common.white, 0.08)
          : alpha(theme.palette.common.black, 0.08),
        cursor: file.url ? "pointer" : "default",
        transition: "background-color 0.15s ease",
        "&:hover": {
          bgcolor: isDark
            ? alpha(theme.palette.common.white, 0.1)
            : alpha(theme.palette.common.black, 0.07),
        },
        maxWidth: 240,
      }}
    >
      <Iconify
        icon={getFileIcon(file.content_type)}
        width={16}
        sx={{ color: "text.secondary", flexShrink: 0 }}
      />
      <Typography
        sx={{
          fontSize: 12,
          lineHeight: 1.4,
          color: "text.primary",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {truncatedName}
      </Typography>
      <Typography
        sx={{
          fontSize: 11,
          color: "text.disabled",
          flexShrink: 0,
        }}
      >
        {formatFileSize(file.size)}
      </Typography>
      {!readOnly && onRemove && (
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            onRemove(file.id);
          }}
          sx={{
            p: 0.25,
            ml: -0.25,
            color: "text.disabled",
            "&:hover": { color: "text.secondary" },
          }}
        >
          <Iconify icon="mdi:close" width={14} />
        </IconButton>
      )}
    </Box>
  );
}

AttachedFileChip.propTypes = {
  file: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    size: PropTypes.number,
    content_type: PropTypes.string,
    url: PropTypes.string,
  }).isRequired,
  onRemove: PropTypes.func,
  readOnly: PropTypes.bool,
};
