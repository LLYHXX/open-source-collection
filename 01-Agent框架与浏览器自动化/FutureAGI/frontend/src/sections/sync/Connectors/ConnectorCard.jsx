import { Box, Card, Typography } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const ConnectorCard = ({ title, icon, onClick }) => {
  return (
    <Card
      sx={{
        display: "flex",
        flexDirection: "column",
        minWidth: "250px",
        gap: 1,
        minHeight: "98px",
        justifyContent: "center",
        alignItems: "center",
        cursor: "pointer",
      }}
      onClick={onClick}
    >
      <Box alt="logo" component="img" src={icon} width={32} height={32} />
      <Typography variant="body2" color="text.secondary">
        {title}
      </Typography>
    </Card>
  );
};

ConnectorCard.propTypes = {
  title: PropTypes.string,
  icon: PropTypes.any,
  onClick: PropTypes.func,
};

export default ConnectorCard;
