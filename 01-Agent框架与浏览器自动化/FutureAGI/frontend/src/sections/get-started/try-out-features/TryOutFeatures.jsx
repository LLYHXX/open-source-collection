import { Box, Typography } from "@mui/material";
import React from "react";
import FeatureCard from "./FeatureCard";
import { featureCardList } from "../constant";

const TryOutFeatures = () => {
  return (
    <Box>
      <Typography
        variant="m2"
        fontWeight={"fontWeightMedium"}
        color={"text.primary"}
      >
        Try out our features
      </Typography>
      <Box
        display={"flex"}
        flexDirection={"row"}
        gap={"12px"}
        sx={{ marginTop: "12px" }}
      >
        {featureCardList.map((item, index) => (
          <FeatureCard
            key={index}
            title={item.title}
            description={item.description}
            imageUrl={item.image}
            imageUrlDark={item.imageDark}
            buttonTitle={item.buttonTitle}
            learnMoreLink={item.learnMoreLink}
            actionLink={item.actionLink}
          />
        ))}
      </Box>
    </Box>
  );
};

export default TryOutFeatures;
