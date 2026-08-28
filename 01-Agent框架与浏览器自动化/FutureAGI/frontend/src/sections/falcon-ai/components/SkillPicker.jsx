import React, { useState } from "react";
import PropTypes from "prop-types";
import Box from "@mui/material/Box";
import ButtonBase from "@mui/material/ButtonBase";
import Typography from "@mui/material/Typography";
import { alpha, useTheme } from "@mui/material/styles";
import Iconify from "src/components/iconify";
import useFalconStore from "../store/useFalconStore";
import SkillEditorDialog from "./SkillEditorDialog";

export default function SkillPicker({ onSkillsChanged }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingSkill, setEditingSkill] = useState(null);

  const skills = useFalconStore((s) => s.skills);
  const setPendingPrompt = useFalconStore((s) => s.setPendingPrompt);

  // Insert `/<slug> ` into the chat input and let ChatInput's pendingPrompt
  // effect handle focus + caret-at-end. Avoids the header SkillBadge chip
  // that `setActiveSkill` would otherwise render — the skill is activated
  // purely via the inline /slug syntax, which the backend already parses.
  const handleSkillClick = (skill) => {
    setPendingPrompt(`/${skill.slug} `);
  };

  const handleCreateClick = () => {
    setEditingSkill(null);
    setEditorOpen(true);
  };

  const handleEditorClose = () => {
    setEditorOpen(false);
    setEditingSkill(null);
  };

  if (!skills || skills.length === 0) {
    return (
      <>
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            py: 1,
          }}
        >
          <ButtonBase
            onClick={handleCreateClick}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 0.75,
              px: 1.5,
              py: 0.75,
              borderRadius: "10px",
              border: "1px dashed",
              borderColor: isDark
                ? alpha(theme.palette.common.white, 0.12)
                : alpha(theme.palette.common.black, 0.12),
              transition: "all 0.15s ease",
              "&:hover": {
                borderColor: isDark
                  ? alpha(theme.palette.common.white, 0.25)
                  : alpha(theme.palette.common.black, 0.25),
                bgcolor: isDark
                  ? alpha(theme.palette.common.white, 0.04)
                  : alpha(theme.palette.common.black, 0.03),
              },
            }}
          >
            <Iconify
              icon="mdi:plus"
              width={14}
              sx={{ color: "text.disabled" }}
            />
            <Typography
              sx={{
                fontSize: 12,
                color: "text.disabled",
                whiteSpace: "nowrap",
              }}
            >
              Create Skill
            </Typography>
          </ButtonBase>
        </Box>

        <SkillEditorDialog
          open={editorOpen}
          skill={editingSkill}
          onClose={handleEditorClose}
          onSaved={onSkillsChanged}
        />
      </>
    );
  }

  return (
    <>
      <Box
        sx={{
          display: "flex",
          gap: 0.75,
          flexWrap: "wrap",
          justifyContent: "center",
          py: 1,
        }}
      >
        {skills.map((skill) => (
          <ButtonBase
            key={skill.id}
            onClick={() => handleSkillClick(skill)}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 0.75,
              px: 1.5,
              py: 0.75,
              borderRadius: "10px",
              border: 1,
              borderColor: isDark
                ? alpha(theme.palette.common.white, 0.1)
                : alpha(theme.palette.common.black, 0.1),
              bgcolor: "transparent",
              transition: "all 0.15s ease",
              "&:hover": {
                bgcolor: isDark
                  ? alpha(theme.palette.common.white, 0.06)
                  : alpha(theme.palette.common.black, 0.04),
                borderColor: isDark
                  ? alpha(theme.palette.common.white, 0.2)
                  : alpha(theme.palette.common.black, 0.2),
              },
            }}
          >
            <Iconify
              icon={skill.icon || "mdi:star-outline"}
              width={14}
              sx={{ color: "text.disabled" }}
            />
            <Typography
              sx={{
                fontSize: 12,
                color: "text.secondary",
                whiteSpace: "nowrap",
              }}
            >
              {skill.name}
            </Typography>
          </ButtonBase>
        ))}

        <ButtonBase
          onClick={handleCreateClick}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 0.75,
            px: 1.5,
            py: 0.75,
            borderRadius: "10px",
            border: "1px dashed",
            borderColor: isDark
              ? alpha(theme.palette.common.white, 0.12)
              : alpha(theme.palette.common.black, 0.12),
            transition: "all 0.15s ease",
            "&:hover": {
              borderColor: isDark
                ? alpha(theme.palette.common.white, 0.25)
                : alpha(theme.palette.common.black, 0.25),
              bgcolor: isDark
                ? alpha(theme.palette.common.white, 0.04)
                : alpha(theme.palette.common.black, 0.03),
            },
          }}
        >
          <Iconify icon="mdi:plus" width={14} sx={{ color: "text.disabled" }} />
          <Typography
            sx={{ fontSize: 12, color: "text.disabled", whiteSpace: "nowrap" }}
          >
            Create Skill
          </Typography>
        </ButtonBase>
      </Box>

      <SkillEditorDialog
        open={editorOpen}
        skill={editingSkill}
        onClose={handleEditorClose}
        onSaved={onSkillsChanged}
      />
    </>
  );
}

SkillPicker.propTypes = {
  onSkillsChanged: PropTypes.func,
};
