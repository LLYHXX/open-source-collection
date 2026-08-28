import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box, IconButton, useTheme, Typography } from "@mui/material";
import { useDropzone } from "react-dropzone";
import SvgColor from "src/components/svg-color";
import DeleteMediaDialog from "src/sections/develop-detail/DataTab/DoubleClickEditCell/ConfirmDelete";
import { useParams } from "react-router";
import logger from "src/utils/logger";
import { enqueueSnackbar } from "notistack";
import TestAudioPlayer from "src/components/custom-audio/TestAudioPlayer";
import { useDevelopDetailContext } from "../../../develop-detail/Context/DevelopDetailContext";

const allowedTypes = [
  "audio/mpeg",
  "audio/mp3",
  "audio/wav",
  "audio/ogg",
  "audio/m4a",
  "audio/aac",
  "audio/flac",
  "audio/webm",
];

const validateFileSize = (file) => {
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    enqueueSnackbar("File size must be below 5 MB", { variant: "error" });
    return false;
  }
  return true;
};

const validateAudioType = (file) => {
  if (
    !allowedTypes.includes(file.type) &&
    !file.name.match(/\.(mp3|wav|ogg|m4a|aac|flac|webm)$/i)
  ) {
    enqueueSnackbar("File must be in an audio format", { variant: "error" });
    return false;
  }
  return true;
};

const processFile = (
  file,
  onCellValueChanged,
  params = {},
  refreshGrid = () => {},
) => {
  if (!validateAudioType(file) || !validateFileSize(file)) {
    return;
  }

  const reader = new FileReader();
  reader.onloadend = () => {
    const base64String = reader.result;
    onCellValueChanged({
      ...params,
      newValue: base64String,
      onSuccess: () => {
        refreshGrid();
      },
    });
  };
  reader.readAsDataURL(file);
};

const AudioCellRenderer = ({
  value,
  cacheKey,
  getWaveSurferInstance,
  storeWaveSurferInstance,
  updateWaveSurferInstance,
  onEditCell,
  onCellValueChanged,
  params,
  editable = false,
}) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isPending] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const { dataset } = useParams();
  const theme = useTheme();
  const { refreshGrid } = useDevelopDetailContext();

  const onDrop = (acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      enqueueSnackbar("File must be in an audio format", {
        variant: "error",
      });
      return;
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      processFile(file, onCellValueChanged, params, refreshGrid);
    }
  };

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: {
      "audio/*": [],
    },
    multiple: false,
    noClick: true,
    noKeyboard: true,
  });

  const handleDelete = () => {
    try {
      onCellValueChanged({ ...params, newValue: null });
      setShowDeleteDialog(false);
    } catch (err) {
      logger.error("An error occurred while deleting the audio:", err);
    }
  };

  const audioData = {
    url: value,
    fileName: "",
    fileType: "",
    size: "",
  };

  return (
    <>
      <Box
        sx={{
          position: "relative",
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-start",
          px: 1,
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {value ? (
          <>
            <Box
              className="audio-control-btn"
              onClick={(e) => e.stopPropagation()}
              sx={{
                maxHeight: "60px",
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <TestAudioPlayer
                audioData={audioData}
                showFileName={false}
                cacheKey={cacheKey}
                getWaveSurferInstance={getWaveSurferInstance}
                storeWaveSurferInstance={storeWaveSurferInstance}
                updateWaveSurferInstance={updateWaveSurferInstance}
              />
            </Box>

            {dataset && editable && (
              <Box
                className="icon-actions"
                sx={{
                  position: "absolute",
                  top: 4,
                  right: 4,
                  display: "flex",
                  height: "30px",
                  opacity: isHovered ? 1 : 0,
                  transition: "opacity 0.2s",
                  zIndex: 2,
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    window.__audioClick = true;
                    onEditCell?.();
                  }}
                  aria-label="edit"
                >
                  <SvgColor
                    src={`/assets/icons/ic_edit.svg`}
                    sx={{
                      width: 16,
                      height: 16,
                      color: theme.palette.text.primary,
                      pointerEvents: "none",
                    }}
                  />
                </IconButton>

                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    window.__audioClick = true;
                    setShowDeleteDialog(true);
                  }}
                  aria-label="delete"
                >
                  <SvgColor
                    src={"/assets/icons/components/ic_delete.svg"}
                    sx={{
                      width: 16,
                      height: 16,
                      color: theme.palette.text.primary,
                      pointerEvents: "none",
                    }}
                  />
                </IconButton>
              </Box>
            )}
          </>
        ) : (
          editable && (
            <Box
              {...getRootProps()}
              sx={{ height: "92%", width: "100%", display: "flex" }}
            >
              <input {...getInputProps()} />
              <Box
                sx={{
                  height: "100%",
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: "8px",
                  border: "1px dashed",
                  borderColor: theme.palette.divider,
                  minHeight: "60px",
                  backgroundColor: isDragActive
                    ? theme.palette.background.neutral
                    : "transparent",
                  position: "relative",
                  textAlign: "center",
                }}
              >
                <Typography
                  variant="s3"
                  color="text.primary"
                  textAlign="center"
                >
                  <label
                    htmlFor="audio-file-upload"
                    style={{ color: "var(--primary-main)", cursor: "pointer" }}
                    onClick={(e) => {
                      e.stopPropagation();
                      window.__audioClick = true;
                      open();
                    }}
                  >
                    Click here
                  </label>{" "}
                  to upload audio file or <br />
                  drop an audio file here
                </Typography>
              </Box>
            </Box>
          )
        )}
      </Box>

      <DeleteMediaDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onDelete={handleDelete}
        isPending={isPending}
        fileName="this audio file"
        fileType="audio"
      />
    </>
  );
};

AudioCellRenderer.propTypes = {
  value: PropTypes.string,
  cacheKey: PropTypes.string,
  getWaveSurferInstance: PropTypes.func,
  storeWaveSurferInstance: PropTypes.func,
  updateWaveSurferInstance: PropTypes.func,
  onEditCell: PropTypes.func,
  onCellValueChanged: PropTypes.func,
  params: PropTypes.object,
  editable: PropTypes.bool,
};

export default React.memo(AudioCellRenderer);
