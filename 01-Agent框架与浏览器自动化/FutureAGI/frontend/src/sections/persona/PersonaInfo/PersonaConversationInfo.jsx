import { Box, Typography } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";
import { ShowComponent } from "src/components/show";
import { extractMultilingualityLanguagesConversationSpeedTagsFromPersona } from "../common";
import { extractBackgroundNoiseFinishedSpeakingSensitivityInterruptSensitivityTagsFromPersona } from "../common";
import PersonaIcons from "../PersonaIcons";

const PersonaConversationInfo = ({ persona }) => {
  const multilingualityLanguagesConversationSpeedTags =
    extractMultilingualityLanguagesConversationSpeedTagsFromPersona(persona);

  const backgroundNoiseFinishedSpeakingSensitivityInterruptSensitivityTags =
    extractBackgroundNoiseFinishedSpeakingSensitivityInterruptSensitivityTagsFromPersona(
      persona,
    );

  return (
    <Box
      sx={{
        padding: "1px",

        borderRadius: 0.5,
      }}
    >
      <Box
        sx={{
          padding: 2,
          backgroundColor: "background.neutral",
          border: "1px solid",
          borderColor: "divider",
          borderRadius: 0.5,
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          height: "100%",
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <PersonaIcons
              imgSrc="/assets/icons/persona/conversation.svg"
              imgStyles={{ width: "24px", height: "24px" }}
            />
            <Typography typography="s1_2" fontWeight="fontWeightMedium">
              Conversation Settings
            </Typography>
          </Box>
        </Box>

        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 1.5,
          }}
        >
          <ShowComponent
            condition={multilingualityLanguagesConversationSpeedTags.length > 0}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                gap: "12px",
                flexWrap: "wrap",
              }}
            >
              {multilingualityLanguagesConversationSpeedTags.map((tag) => (
                <Box
                  key={tag[0]}
                  sx={{
                    padding: "4px 12px",
                    borderRadius: "2px",
                    border: "1px solid",
                    borderColor: "action.focus",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    width: "fit-content",
                    background: "background.paper",
                  }}
                >
                  <Typography typography="s2" fontWeight="fontWeightMedium">
                    {tag[0]}:
                  </Typography>
                  <Typography typography="s2" fontWeight="fontWeightNormal">
                    {tag[1]}
                  </Typography>
                </Box>
              ))}
            </Box>
          </ShowComponent>
          <ShowComponent
            condition={
              backgroundNoiseFinishedSpeakingSensitivityInterruptSensitivityTags.length >
              0
            }
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                gap: "12px",
                flexWrap: "wrap",

                padding: "4px 12px",
                borderRadius: "2px",
                border: "1px solid",
                borderColor: "action.hover",
                width: "fit-content",
              }}
            >
              {backgroundNoiseFinishedSpeakingSensitivityInterruptSensitivityTags.map(
                (tag) => (
                  <Box
                    key={tag[0]}
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      flexWrap: "wrap",
                      background: "background.paper",
                      width: "354px",
                    }}
                  >
                    <Typography typography="s2" fontWeight="fontWeightMedium">
                      {tag[0]}:
                    </Typography>
                    <Typography typography="s2" fontWeight="fontWeightNormal">
                      {tag[1]}
                    </Typography>
                  </Box>
                ),
              )}
            </Box>
          </ShowComponent>
          {multilingualityLanguagesConversationSpeedTags.length === 0 &&
            backgroundNoiseFinishedSpeakingSensitivityInterruptSensitivityTags.length ===
              0 && (
              <Typography>
                You have not added any conversation settings yet
              </Typography>
            )}
        </Box>
      </Box>
    </Box>
  );
};

PersonaConversationInfo.propTypes = {
  viewOptions: PropTypes.shape({
    name: PropTypes.bool,
    description: PropTypes.bool,
  }),
  multiple: PropTypes.bool,

  title: PropTypes.string,
  persona: PropTypes.object,
};

export default PersonaConversationInfo;
