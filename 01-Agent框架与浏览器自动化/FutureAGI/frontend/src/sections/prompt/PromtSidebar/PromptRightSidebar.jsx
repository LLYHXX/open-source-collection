import React, { useState } from "react";
import { Box, Button, Drawer, Typography } from "@mui/material";
import { useNavigate } from "react-router";
import Iconify from "src/components/iconify";
import { useMutation } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { enqueueSnackbar } from "notistack";
import ConfirmDialog from "src/components/custom-dialog/confirm-dialog";
import { trackEvent, Events, PropertyName } from "src/utils/Mixpanel";

import GeneratePrompt from "../PromptDrawer/GeneratePrompt";
import ImprovePromptDrawer from "../NewPrompt/ImprovePrompt/ImprovePrompt";
import logger from "src/utils/logger";

const PROMPT_MANAGEMENT_CARD = [
  {
    icon: "humbleicons:prompt",
    text: "Write a prompt from scratch",
    navigate: "/dashboard/prompt/add/:id",
    showSidebar: false,
  },
  {
    icon: "fluent:magic-wand-16-regular",
    text: "Generate a prompt",
    navigate: "/dashboard/prompt/add/generate",
    showSidebar: false,
  },
  {
    icon: "ph:flow-arrow",
    text: "Improve an existing prompt",
    navigate: "/dashboard/prompt/add/:id",
    showSidebar: true,
  },
];

const PromptRightSidebar = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [openImprovePrompt, setOpenImprovePrompt] = useState(false);
  const [openModal, setOpenModal] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  const handleClose = () => {
    if (isDirty) {
      setOpenModal(true);
    } else {
      if (openImprovePrompt) {
        setOpenImprovePrompt(false);
      } else {
        setOpen(false);
      }
    }
  };
  const handleImprovePromptClose = () => {
    if (isDirty) {
      setOpenModal(true);
    } else {
      setOpenImprovePrompt(false);
    }
  };

  const handleConfirmClose = () => {
    setOpenModal(false);
    if (openImprovePrompt) {
      setOpenImprovePrompt(false);
    } else {
      setOpen(false);
    }
    setIsDirty(false);
  };

  const handleCancelClose = () => {
    setOpenModal(false);
  };

  const { mutate: createDraft } = useMutation({
    mutationFn: (body) =>
      axios.post(endpoints.develop.runPrompt.createPromptDraft, body),
    onSuccess: (data) => {
      enqueueSnackbar("Prompt created successfully.", {
        variant: "success",
      });
      navigate(`/dashboard/prompt/add/${data?.data?.result?.rootTemplate}`, {
        state: { title: "Untitled" },
      });
    },
  });

  const handleCreateDraft = () => {
    const payload = {
      name: "",
      prompt_config: [
        {
          messages: [
            {
              role: "system",
              content: [
                {
                  type: "text",
                  text: "",
                },
              ],
            },
            {
              role: "user",
              content: [
                {
                  type: "text",
                  text: "",
                },
              ],
            },
          ],
        },
      ],
    };
    createDraft(payload);
  };

  const handleApply = async (output) => {
    try {
      const payload = {
        name: "",
        description: "This is a draft template for testing purposes.",
        prompt_config: [
          {
            messages: [
              {
                role: "user",
                content: [
                  {
                    type: "text",
                    text: output,
                  },
                ],
              },
            ],
          },
        ],
      };

      const response = await axios.post(
        endpoints.develop.runPrompt.createPromptDraft,
        payload,
      );
      navigate(`/dashboard/prompt/add/${response.data.result.id}`);
      enqueueSnackbar("Apply successfull.", {
        variant: "success",
      });
    } catch (error) {
      logger.error("Failed to apply prompt", error);
      enqueueSnackbar("Failed to Apply.", {
        variant: "error",
      });
    }
  };

  const handleSetIsDirty = (dirty) => {
    setIsDirty(dirty);
  };

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        flexWrap: "wrap",
        flexDirection: "column",
        justifyContent: "center",
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          flexDirection: "column",
          alignItems: "center",
          margin: "0 0 40px 0",
        }}
      >
        <img src="/favicon/logo.svg" alt="logo" height={52} width={52} />
        <Typography
          color="text.primary"
          variant="h5"
          sx={{ margin: "28px 0 20px 0" }}
        >
          Prompt Management
        </Typography>
        <Typography
          color="text.primary"
          variant="subtitle2"
          fontWeight={"fontWeightRegular"}
        >
          Generate, test and refine prompts for your language Models
        </Typography>
      </Box>

      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          width: "100%",
          gap: "12px",
          // padding: "20px 0 0 0",
          minHeight: "160px",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {PROMPT_MANAGEMENT_CARD.map((card) => (
          <Button
            key={card.text}
            sx={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center",
              padding: "17px",
              width: "100%",
              gap: "15px",
              maxWidth: "293px",
              minHeight: "127px",
              border: "1px solid",
              borderColor: "divider",
              borderRadius: "8px",
              "&:hover": {
                border: "1px solid rgba(183, 102, 237, 1)",
                height: "146px",
                background: "background.paper",
              },
            }}
            onClick={() => {
              if (card.text == "Write a prompt from scratch") {
                trackEvent(Events.promptMethodClicked, {
                  [PropertyName.method]: card.text,
                });
                handleCreateDraft();
              } else if (card.text == "Improve an existing prompt") {
                trackEvent(Events.promptMethodClicked, {
                  [PropertyName.method]: card.text,
                });
                setOpenImprovePrompt(true);
              } else {
                trackEvent(Events.promptMethodClicked, {
                  [PropertyName.method]: card.text,
                });
                setOpen(true);
              }
            }}
          >
            <Iconify
              icon={card.icon}
              sx={{ color: "#B766ED" }}
              width={45}
              height={45}
            />
            <Typography
              color="text.primary"
              variant="body1"
              fontWeight={"fontWeightMedium"}
            >
              {card.text}
            </Typography>
          </Button>
        ))}
      </Box>
      <Drawer
        anchor="right"
        open={openImprovePrompt}
        onClose={handleClose}
        PaperProps={{
          sx: {
            height: "100vh",
            width: "calc(100% - 450px)",
            position: "fixed",
            zIndex: 1,
            borderRadius: "10px",
            backgroundColor: "background.paper",
          },
        }}
        ModalProps={{
          BackdropProps: {
            style: { backgroundColor: "transparent" },
          },
        }}
      >
        <ImprovePromptDrawer
          onClose={handleImprovePromptClose}
          onApply={handleApply}
          setIsDirty={handleSetIsDirty}
        />
      </Drawer>
      <Drawer
        anchor="right"
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            height: "100vh",
            width: "calc(100% - 450px)",
            position: "fixed",
            zIndex: 1,
            borderRadius: "10px",
            backgroundColor: "background.paper",
          },
        }}
        ModalProps={{
          BackdropProps: {
            style: { backgroundColor: "transparent" },
          },
        }}
      >
        <GeneratePrompt
          open={open}
          onClose={handleClose}
          onApply={handleApply}
          setIsDirty={handleSetIsDirty}
        />
      </Drawer>
      <ConfirmDialog
        content="Are you sure you want to proceed?"
        action={
          <Button
            size="small"
            variant="contained"
            color="error"
            onClick={handleConfirmClose}
          >
            Confirm
          </Button>
        }
        open={openModal}
        onClose={handleCancelClose}
        title="Confirm Action"
        message="Are you sure you want to proceed?
        This action can cause your data lost."
      />
    </Box>
  );
};

export default PromptRightSidebar;
