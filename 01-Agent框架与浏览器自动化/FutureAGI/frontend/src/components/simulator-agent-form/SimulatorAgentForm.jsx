import {
  Box,
  Button,
  Drawer,
  Divider,
  IconButton,
  Tab,
  Tabs,
  Typography,
  useTheme,
} from "@mui/material";
import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import Iconify from "../iconify";
import HeadingAndSubheading from "../HeadingAndSubheading/HeadingAndSubheading";
import { useForm } from "react-hook-form";
import BasicDetailsForm from "./BasicDetailsForm";
import VoiceAndSpeechForm from "./VoiceAndSpeechForm";
import ConversationForm from "./ConversationForm";
import { ShowComponent } from "../show";
import { zodResolver } from "@hookform/resolvers/zod";
import { formSchema } from "./validation";
import { Events, PropertyName, trackEvent } from "src/utils/Mixpanel";

const tabEventMap = {
  "Basic Settings": Events.simulatorAgentBasicSettingClicked,
  "Voice & Speech": Events.simulatorAgentVoiceSpeechClicked,
  Conversation: Events.simulatorAgentConversationClicked,
};

const sections = ["Basic Settings", "Voice & Speech", "Conversation"];

const SimulatorAgentForm = ({
  open,
  onClose,
  heading,
  saveLabel,
  subHeading,
  onSubmit,
  defaultValues,
}) => {
  const [activeTab, setActiveTab] = useState("Basic Settings");
  const { control, formState, handleSubmit, reset } = useForm({
    defaultValues: defaultValues,
    resolver: zodResolver(formSchema),
  });
  const theme = useTheme();

  function handleClose() {
    onClose();
    reset(defaultValues);
    setActiveTab("Basic Settings");
  }

  useEffect(() => {
    reset(defaultValues);
  }, [defaultValues]);

  const handleTrackTabChange = (tab) => {
    const event = tabEventMap[tab];
    if (event) {
      trackEvent(event, {
        [PropertyName.click]: true,
      });
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={handleClose}
      PaperProps={{
        sx: {
          height: "100vh",
          position: "fixed",
          zIndex: 2,
          boxShadow: "-10px 0px 100px #00000035",
          borderRadius: "10px",
          backgroundColor: "background.paper",
          overflow: "visible",
          padding: 2,
        },
      }}
      ModalProps={{
        BackdropProps: {
          style: { backgroundColor: "transparent" },
        },
      }}
    >
      <form
        onSubmit={handleSubmit(onSubmit)}
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 3,
          }}
        >
          <HeadingAndSubheading
            heading={
              <Typography typography={"m2"} fontWeight={"fontWeightMedium"}>
                {heading}
              </Typography>
            }
            subHeading={<Typography typography={"s1"}>{subHeading}</Typography>}
          ></HeadingAndSubheading>

          <IconButton onClick={handleClose}>
            <Iconify icon="eva:close-fill" />
          </IconButton>
        </Box>

        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
            overflow: "hidden",
          }}
        >
          <Tabs
            variant="fullWidth"
            value={activeTab}
            textColor="primary"
            indicatorColor="primary"
            TabIndicatorProps={{
              style: {
                backgroundColor: theme.palette.primary.main,
              },
            }}
            sx={{
              width: "100%",
              minHeight: 0,
              "& .MuiTab-root": {
                margin: "0 !important",
                fontWeight: "600",
                typography: "s2",
                color: "primary.main",
                "&:not(.Mui-selected)": {
                  color: "text.disabled",
                  fontWeight: "500",
                },
              },
            }}
          >
            {sections.map((label) => (
              <Tab
                key={label}
                value={label}
                label={label}
                onClick={() => {
                  handleTrackTabChange(label);
                  setActiveTab(label);
                }}
              />
            ))}
          </Tabs>
          <Divider sx={{ mb: 2 }} />

          <Box
            sx={{
              flex: 1,
              overflow: "auto",
              pr: 1,
            }}
          >
            <ShowComponent condition={activeTab === "Basic Settings"}>
              <BasicDetailsForm control={control} errors={formState.errors} />
            </ShowComponent>
            <ShowComponent condition={activeTab === "Voice & Speech"}>
              <VoiceAndSpeechForm control={control} errors={formState.errors} />
            </ShowComponent>
            <ShowComponent condition={activeTab === "Conversation"}>
              <ConversationForm control={control} errors={formState.errors} />
            </ShowComponent>
          </Box>
        </Box>

        <Box
          sx={{
            mt: 3,
            pt: 2,
            borderTop: 1,
            borderColor: "divider",
            display: "flex",
            justifyContent: "flex-end",
          }}
        >
          <Button
            variant="contained"
            color="primary"
            disabled={!formState.isValid}
            sx={{
              width: "200px",
            }}
            type="submit"
          >
            {saveLabel}
          </Button>
        </Box>
      </form>
    </Drawer>
  );
};

export default SimulatorAgentForm;

SimulatorAgentForm.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func,
  heading: PropTypes.string,
  subHeading: PropTypes.string,
  saveLabel: PropTypes.string,
  onSubmit: PropTypes.func,
  defaultValues: PropTypes.object,
};
