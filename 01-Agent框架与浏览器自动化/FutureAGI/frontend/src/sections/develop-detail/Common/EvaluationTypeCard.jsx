import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import Label from "src/components/label";
import { formatEvalType } from "src/utils/utils";

const EvaluationTypeCard = ({ title, subTitle, onClick, tags }) => {
  return (
    <Box
      sx={{
        paddingY: "15px",
        paddingX: "18px",
        display: "flex",
        flexDirection: "column",
        gap: 1,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        cursor: "pointer",
      }}
      onClick={onClick}
    >
      <Typography variant="body2" fontWeight={400}>
        {title}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {subTitle}
      </Typography>
      <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", paddingTop: 3 }}>
        {tags.map((tag) => (
          <Label
            key={tag}
            variant="soft"
            color="primary"
            sx={{
              fontWeight: 500,
            }}
          >
            {formatEvalType(tag)}
          </Label>
        ))}
      </Box>
    </Box>
  );
};

EvaluationTypeCard.propTypes = {
  title: PropTypes.string.isRequired,
  subTitle: PropTypes.string.isRequired,
  onClick: PropTypes.func,
  tags: PropTypes.array,
};

export default EvaluationTypeCard;
