import React from "react";
import { Typography, Link } from "@mui/material";
import PropTypes from "prop-types";

const LinkifiedTypography = ({ text, ...typographyProps }) => {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlRegex);

  return (
    <Typography component="span" {...typographyProps}>
      {parts.map((part, index) => {
        // Check if the part is a valid URL
        if (urlRegex.test(part)) {
          // Remove trailing punctuation like .,),] etc.
          const cleanUrl = part.replace(/[\s'")\],.!?]*$/, "");
          const trailing = part.slice(cleanUrl.length);

          return (
            <React.Fragment key={index}>
              <Link
                color="inherit"
                href={cleanUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                {cleanUrl}
              </Link>
              {trailing}
            </React.Fragment>
          );
        } else {
          return <React.Fragment key={index}>{part}</React.Fragment>;
        }
      })}
    </Typography>
  );
};

LinkifiedTypography.propTypes = {
  text: PropTypes.string.isRequired,
};

export default LinkifiedTypography;
