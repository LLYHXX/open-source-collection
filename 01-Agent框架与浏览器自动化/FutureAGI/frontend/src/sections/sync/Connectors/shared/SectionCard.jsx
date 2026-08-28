import { Box, Button, Card, Divider, Typography } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const SectionCard = ({
  title,
  children,
  onActionButtonClick,
  actionButtonText,
}) => {
  return (
    <Card sx={{ display: "flex", flexDirection: "column" }}>
      <Box
        sx={{
          padding: "20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography fontWeight={700} fontSize={14} color="text.primary">
          {title}
        </Typography>
        {onActionButtonClick ? (
          <Button variant="soft" size="small" onClick={onActionButtonClick}>
            {actionButtonText}
          </Button>
        ) : null}
      </Box>
      <Divider />
      {children}
    </Card>
  );
};

SectionCard.propTypes = {
  title: PropTypes.string,
  children: PropTypes.any,
  onActionButtonClick: PropTypes.func,
  actionButtonText: PropTypes.string,
};

export default SectionCard;
