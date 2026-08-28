import { extractChatSettingsFromPersona } from "../common";
import { Box, Typography } from "@mui/material";
import PersonaIcons from "../PersonaIcons";
import { ShowComponent } from "src/components/show";
import PropTypes from "prop-types";

const PersonaChatSettingsInfo = ({ persona }) => {
  const chatSettings = extractChatSettingsFromPersona(persona);
  const chatSettingsEntries = Object.entries(chatSettings);

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
        {/* Header */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <PersonaIcons
              imgSrc="/assets/icons/ic_chat_single.svg"
              imgStyles={{ width: "24px", height: "24px" }}
            />
            <Typography typography="s1_2" fontWeight="fontWeightMedium">
              Chat Settings
            </Typography>
          </Box>
        </Box>

        {/* Content */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          <ShowComponent condition={chatSettingsEntries.length > 0}>
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                gap: 1,
                flexWrap: "wrap",
              }}
            >
              {chatSettingsEntries.map(([label, value]) => (
                <Box
                  key={label}
                  sx={{
                    padding: "4px 12px",
                    borderRadius: "2px",
                    border: "1px solid",
                    borderColor: "action.hover",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    width: "fit-content",
                    background: "background.paper",
                  }}
                >
                  <Typography typography="s2" fontWeight="fontWeightMedium">
                    {label}:
                  </Typography>
                  <Typography typography="s2" fontWeight="fontWeightNormal">
                    {value}
                  </Typography>
                </Box>
              ))}
            </Box>
          </ShowComponent>

          {chatSettingsEntries.length === 0 && (
            <Typography>You have not added any chat settings yet</Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
};
export default PersonaChatSettingsInfo;
PersonaChatSettingsInfo.propTypes = {
  persona: PropTypes.object,
};
