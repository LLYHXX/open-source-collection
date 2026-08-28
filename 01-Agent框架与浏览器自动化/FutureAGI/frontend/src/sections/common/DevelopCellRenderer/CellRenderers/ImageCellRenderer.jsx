import React, { useEffect, useRef, useState } from "react";
import { Box, IconButton, Typography, useTheme } from "@mui/material";
import { useDropzone } from "react-dropzone";
import RenderMeta from "../RenderMeta";
import { commonPropTypes } from "./cellRendererHelper";
import SvgColor from "src/components/svg-color";
import DeleteMediaDialog from "src/sections/develop-detail/DataTab/DoubleClickEditCell/ConfirmDelete";
import { useParams } from "react-router";
import logger from "src/utils/logger";
import { enqueueSnackbar } from "notistack";
import GridIcon from "src/components/gridIcon/GridIcon";
import { ShowComponent } from "src/components/show";

const validateFileSize = (file) => {
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    enqueueSnackbar("File size must be below 5 mb", { variant: "error" });
    return false;
  }
  return true;
};

const ImageCellRenderer = ({
  value,
  _valueReason,
  _formattedValueReason,
  originType,
  metadata,
  setImageUrl,
  onEditCell,
  params,
  onCellValueChanged,
  editable = false,
  valueInfos,
  isHover,
}) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isPending] = useState(false);
  const outerBoxRef = useRef(null);
  const [, setMaxWidth] = useState(180);
  const { dataset } = useParams();

  useEffect(() => {
    if (outerBoxRef.current) {
      const height = outerBoxRef.current.offsetHeight;
      if (height <= 97) {
        setMaxWidth(89);
      } else if (height <= 137) {
        setMaxWidth(129);
      } else if (height <= 177) {
        setMaxWidth(169);
      } else {
        setMaxWidth(180);
      }
    }
  }, [value]);

  const processFile = (file) => {
    if (!validateFileSize(file)) {
      return;
    }
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = reader.result;
      const img = new window.Image();
      img.src = base64String;
      onCellValueChanged({ ...params, newValue: base64String });
    };
    reader.readAsDataURL(file);
  };

  const onDrop = (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      processFile(file);
    }
  };

  // Only enable dropzone when there's no existing image
  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    onDropRejected: () => {
      enqueueSnackbar(
        "Unsupported format. Supported formats: JPEG, PNG, WebP, BMP, TIFF",
        { variant: "error" },
      );
    },
    accept: {
      "image/jpeg": [],
      "image/png": [],
      "image/webp": [],
      "image/bmp": [],
      "image/tiff": [],
    },
    multiple: false,
    noClick: true,
    noKeyboard: true,
    disabled: Boolean(value), // Disable when there's already an image
  });

  const handleDelete = () => {
    try {
      onCellValueChanged({ ...params, newValue: null });
      setShowDeleteDialog(false);
    } catch (err) {
      logger.error("An error occurred while deleting the image:", err);
    }
  };

  const theme = useTheme();
  return (
    <>
      {/* <CustomTooltip
        show={originType !== "run_prompt" && Boolean(valueReason?.length)}
        title={formattedValueReason()}
        enterDelay={500}
        enterNextDelay={500}
        leaveDelay={100}
        arrow
        slotProps={tooltipSlotProp}
      > */}
      <Box
        ref={outerBoxRef}
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          position: "relative",
        }}
      >
        <Box
          sx={{
            display: "flex",
            height: "100%",
            justifyContent: "flex-start",
            padding: "4px 8px",
            position: "relative",
            "&:hover .icon-actions": {
              opacity: 1,
            },
          }}
        >
          {value ? (
            <Box sx={{ height: "100%", width: "100%", display: "flex" }}>
              <GridIcon
                height="100%"
                src={value}
                alt=""
                onClick={(e) => {
                  e.stopPropagation();
                  setImageUrl?.(value);
                }}
                onMouseEnter={(e) => {
                  window.__imageClick = true;
                  e.stopPropagation();
                }}
                onMouseLeave={(e) => {
                  window.__imageClick = false;
                  e.stopPropagation();
                }}
                sx={{
                  cursor: "pointer",
                  borderRadius: "8px",
                  maxWidth: "180px",
                  width: "100%",
                  height: "100%",
                }}
              />
            </Box>
          ) : (
            dataset &&
            editable && (
              <Box
                {...getRootProps()}
                sx={{ height: "100%", width: "100%", display: "flex" }}
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
                      htmlFor="file-upload"
                      style={{
                        color: "var(--primary-main)",
                        cursor: "pointer",
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        window.__imageClick = true;
                        open();
                      }}
                    >
                      Click here
                    </label>{" "}
                    to upload image file or <br />
                    drop an image file here
                  </Typography>
                </Box>
              </Box>
            )
          )}

          {dataset && value && editable && (
            <Box
              className="icon-actions"
              sx={{
                position: "absolute",
                top: 4,
                right: 4,
                display: "flex",
                height: "30px",
                opacity: 0,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  window.__imageClick = true;
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
                    PointerEvents: "none",
                  }}
                />
              </IconButton>

              {value && (
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    window.__imageClick = true;
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
                      PointerEvents: "none",
                    }}
                  />
                </IconButton>
              )}
            </Box>
          )}
        </Box>
        <ShowComponent condition={isHover && originType === "run_prompt"}>
          <Box
            sx={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              padding: "4px 8px",
              backgroundColor: "background.neutral",
            }}
          >
            <RenderMeta
              originType={originType}
              meta={metadata}
              valuesInfo={valueInfos}
            />
          </Box>
        </ShowComponent>
      </Box>
      {/* </CustomTooltip> */}
      <DeleteMediaDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onDelete={handleDelete}
        isPending={isPending}
        fileName="this image"
        fileType="image"
      />
    </>
  );
};

ImageCellRenderer.propTypes = {
  ...commonPropTypes,
};

export default React.memo(ImageCellRenderer);
