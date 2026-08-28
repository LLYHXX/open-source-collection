import React, { useState } from "react";
import { Box, Typography, IconButton, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import Iconify from "src/components/iconify";
import DevelopDataNotificationModal from "./DevelopDataNotificationModal";
import { ShowComponent } from "src/components/show";
import { useMutation } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { useParams } from "react-router";

const UploadProgressNotification = ({ status, showReason, onClose }) => {
  const [showWarningModal, setShowWarningModal] = useState(false);
  const theme = useTheme();

  const { dataset } = useParams();

  const { mutate: updateDataset } = useMutation({
    mutationFn: (d) => axios.put(endpoints.develop.updateDataset(dataset), d),
  });

  const onWarningClose = () => {
    setShowWarningModal(false);
  };

  const onBannerDismiss = () => {
    //@ts-ignore
    updateDataset({
      dataset_config: {
        dismiss_banner: true,
      },
    });

    onClose();
  };

  return (
    <>
      <ShowComponent
        condition={status?.datasetStatus == "PartialUploadProgress"}
      >
        <Box
          sx={{
            height: "75px",
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            p: "14px",
            borderColor: "divider",
            border: `1px solid ${theme.palette.blue[200]}`,
            borderRadius: "4px",
            backgroundColor: theme.palette.blue.o5,
            mb: 1.5,
          }}
        >
          <Box
            sx={{
              display: "flex",
              width: "100%",
              alignItems: "center",
              gap: 1.5,
            }}
          >
            <Box width="100%">
              <Box
                sx={{
                  width: "100%",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    gap: "8px",
                    alignItems: "center",
                  }}
                >
                  <Iconify
                    icon="solar:clock-circle-linear"
                    width={20}
                    height={20}
                    sx={{
                      color: theme.palette.blue[500],
                    }}
                  />
                  <Typography
                    variant="body2"
                    sx={{
                      fontSize: "14px",
                      fontWeight: 600,
                      color: theme.palette.blue[500],
                    }}
                  >
                    {"Partial Upload in Progress"}
                  </Typography>
                </Box>
                <IconButton onClick={onBannerDismiss} size="small">
                  <Iconify
                    icon="akar-icons:cross"
                    width={20}
                    height={20}
                    sx={{
                      color: "text.primary",
                    }}
                  />
                </IconButton>
              </Box>
              <Typography
                variant="caption"
                fontWeight={400}
                lineHeight={"18px"}
                fontSize={"12px"}
                color={theme.palette.blue[500]}
              >
                {
                  "We've fetched some data from your CSV, and the extraction process is still running."
                }
              </Typography>
            </Box>
          </Box>
        </Box>
      </ShowComponent>
      <ShowComponent
        condition={status?.datasetStatus == "PartialDataExtracted"}
      >
        <Box
          sx={{
            height: "75px",
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            p: "14px",
            borderColor: "divider",
            border: `1px solid ${theme.palette.orange[200]}`,
            borderRadius: "4px",
            backgroundColor: theme.palette.orange.o5,
            mb: 1.5,
          }}
        >
          <Box
            sx={{
              display: "flex",
              width: "100%",
              alignItems: "center",
              gap: 1.5,
            }}
          >
            <Box width="100%">
              <Box
                sx={{
                  width: "100%",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    gap: "8px",
                    alignItems: "center",
                  }}
                >
                  <Iconify
                    icon="tabler:info-circle"
                    width={20}
                    height={20}
                    sx={{
                      color: theme.palette.orange[500],
                    }}
                  />
                  <Typography
                    variant="body2"
                    lineHeight={"22px"}
                    sx={{
                      fontSize: "14px",
                      fontWeight: 600,
                      color: theme.palette.orange[500],
                    }}
                  >
                    {"Partial Data Extracted"}
                  </Typography>
                </Box>
                <IconButton onClick={onBannerDismiss} size="small">
                  <Iconify
                    icon="akar-icons:cross"
                    width={20}
                    height={20}
                    sx={{
                      color: "text.primary",
                    }}
                  />
                </IconButton>
              </Box>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  width: "100%",
                }}
              >
                <Typography
                  variant="caption"
                  fontSize={"12px"}
                  fontWeight={400}
                  lineHeight={"18px"}
                  color={theme.palette.orange[500]}
                >
                  {
                    "We’ve extracted some data from your CSV, but a few items couldn’t be processed."
                  }
                  &nbsp;
                </Typography>
                {showReason && (
                  <Typography
                    variant="caption"
                    fontSize={"12px"}
                    lineHeight={"18px"}
                    fontWeight={500}
                    color={theme.palette.orange[800]}
                    sx={{
                      textDecoration: "underline",
                      cursor: "pointer",
                    }}
                    onClick={() => setShowWarningModal(true)}
                  >
                    Check reasons
                  </Typography>
                )}
              </Box>
            </Box>
          </Box>
        </Box>
      </ShowComponent>
      <DevelopDataNotificationModal
        open={showWarningModal}
        onClose={onWarningClose}
        onClick={onWarningClose}
        data={status}
      />
    </>
  );
};

UploadProgressNotification.propTypes = {
  showReason: PropTypes.bool,
  onClose: PropTypes.func,
  status: PropTypes.string,
};

export default UploadProgressNotification;
