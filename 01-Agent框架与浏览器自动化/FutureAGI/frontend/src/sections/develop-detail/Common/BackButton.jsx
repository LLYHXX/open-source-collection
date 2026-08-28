import React from "react";
import { Box, Button, styled, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import Iconify from "src/components/iconify";
import PropTypes from "prop-types";
import { palette } from "src/theme/palette";

const CustomBackButton = styled(Button)({
  borderWidth: "1px",
  borderColor: palette("light").black["o5"],
  borderRadius: "4px",
});

const BackButton = ({ text = "", onBack }) => {
  const navigate = useNavigate();

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate("/dashboard/projects/observe");
    }
  };

  return (
    <Box display="flex" alignItems="center" borderRadius={"4px"} gap="4px">
      <CustomBackButton
        size="small"
        startIcon={
          <Iconify
            icon="formkit:left"
            width={16}
            height={16}
            color={"text.primary"}
          />
        }
        onClick={handleBack}
        variant="outlined"
        sx={{
          color: "text.primary",
          padding: "4px 12px",
          height: "30px",
          typography: "s1",
          border: "1px solid",
          borderColor: "divider",
          fontWeight: "fontWeightMedium",
          "& .MuiButton-startIcon": {
            marginRight: "4px",
          },
        }}
      >
        Back
      </CustomBackButton>

      <Typography
        variant="m1"
        color={"text.primary"}
        fontWeight="fontWeightBold"
      >
        {text}
      </Typography>
    </Box>
  );
};

BackButton.propTypes = {
  text: PropTypes.string,
  onBack: PropTypes.func,
};

export default BackButton;
