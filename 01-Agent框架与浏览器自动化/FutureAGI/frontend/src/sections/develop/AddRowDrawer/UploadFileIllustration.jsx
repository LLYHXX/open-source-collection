import React from "react";
import PropTypes from "prop-types";
import { useTheme } from "@mui/material/styles";

const UploadedFileIllustration = ({ width = 131, height = 152 }) => {
  const theme = useTheme();

  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 131 152"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g filter="url(#filter0_di_1589_121036)">
        <rect
          x="8"
          y="8"
          width="98.8235"
          height="120"
          rx="12"
          fill={theme.palette.background.paper}
        />
      </g>
      <g filter="url(#filter1_di_1589_121036)">
        <path
          d="M22.1177 32.769C22.1177 30.7859 23.7271 29.1765 25.7101 29.1765H52.0547C54.0377 29.1765 55.6471 30.7859 55.6471 32.769V37.5589C55.6471 39.5419 54.0377 41.1513 52.0547 41.1513C50.0716 41.1513 48.4622 39.5419 48.4622 37.5589V36.3614H42.4748V55.5211C44.4578 55.5211 46.0673 57.1305 46.0673 59.1135C46.0673 61.0965 44.4578 62.7059 42.4748 62.7059H35.2899C33.3069 62.7059 31.6975 61.0965 31.6975 59.1135C31.6975 57.1305 33.3069 55.5211 35.2899 55.5211V36.3614H29.3025V37.5589C29.3025 39.5419 27.6931 41.1513 25.7101 41.1513C23.7271 41.1513 22.1177 39.5419 22.1177 37.5589V32.769Z"
          fill={theme.palette.primary.main}
        />
      </g>
      <rect
        opacity="0.4"
        x="66.2354"
        y="29.1765"
        width="24.7059"
        height="8.82353"
        rx="4.41176"
        fill={theme.palette.primary.dark}
      />
      <rect
        opacity="0.24"
        x="66.2354"
        y="41.5293"
        width="24.7059"
        height="8.82353"
        rx="4.41176"
        fill={theme.palette.primary.dark}
      />
      <rect
        opacity="0.16"
        x="66.2354"
        y="53.8823"
        width="24.7059"
        height="8.82353"
        rx="4.41176"
        fill={theme.palette.warning.dark}
      />
      <rect
        opacity="0.16"
        x="22.1177"
        y="73.2942"
        width="70.5882"
        height="8.82353"
        rx="4.41176"
        fill={theme.palette.primary.dark}
      />
      <rect
        opacity="0.16"
        x="22.1177"
        y="85.647"
        width="70.5882"
        height="8.82353"
        rx="4.41176"
        fill={theme.palette.primary.dark}
      />
      <defs>
        <filter
          id="filter0_di_1589_121036"
          x="0"
          y="0"
          width="130.824"
          height="152"
          filterUnits="userSpaceOnUse"
          colorInterpolationFilters="sRGB"
        >
          <feFlood floodOpacity="0" result="BackgroundImageFix" />
          <feColorMatrix
            in="SourceAlpha"
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
            result="hardAlpha"
          />
          <feOffset dx="8" dy="8" />
          <feGaussianBlur stdDeviation="8" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0.772549 0 0 0 0 0.792157 0 0 0 0 0.819608 0 0 0 0.16 0"
          />
          <feBlend
            mode="normal"
            in2="BackgroundImageFix"
            result="effect1_dropShadow_1589_121036"
          />
          <feBlend
            mode="normal"
            in="SourceGraphic"
            in2="effect1_dropShadow_1589_121036"
            result="shape"
          />
          <feColorMatrix
            in="SourceAlpha"
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
            result="hardAlpha"
          />
          <feOffset dx="-2" dy="-2" />
          <feGaussianBlur stdDeviation="2" />
          <feComposite in2="hardAlpha" operator="arithmetic" k2="-1" k3="1" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0.772549 0 0 0 0 0.792157 0 0 0 0 0.819608 0 0 0 0.48 0"
          />
          <feBlend
            mode="normal"
            in2="shape"
            result="effect2_innerShadow_1589_121036"
          />
        </filter>
        <filter
          id="filter1_di_1589_121036"
          x="18.1177"
          y="25.1765"
          width="49.5293"
          height="49.5293"
          filterUnits="userSpaceOnUse"
          colorInterpolationFilters="sRGB"
        >
          <feFlood floodOpacity="0" result="BackgroundImageFix" />
          <feColorMatrix
            in="SourceAlpha"
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
            result="hardAlpha"
          />
          <feOffset dx="4" dy="4" />
          <feGaussianBlur stdDeviation="4" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0.470588 0 0 0 0 0.403922 0 0 0 0.16 0"
          />
          <feBlend
            mode="normal"
            in2="BackgroundImageFix"
            result="effect1_dropShadow_1589_121036"
          />
          <feBlend
            mode="normal"
            in="SourceGraphic"
            in2="effect1_dropShadow_1589_121036"
            result="shape"
          />
          <feColorMatrix
            in="SourceAlpha"
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
            result="hardAlpha"
          />
          <feOffset dx="-1" dy="-1" />
          <feGaussianBlur stdDeviation="1" />
          <feComposite in2="hardAlpha" operator="arithmetic" k2="-1" k3="1" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0.470588 0 0 0 0 0.403922 0 0 0 0.48 0"
          />
          <feBlend
            mode="normal"
            in2="shape"
            result="effect2_innerShadow_1589_121036"
          />
        </filter>
      </defs>
    </svg>
  );
};

UploadedFileIllustration.propTypes = {
  width: PropTypes.number,
  height: PropTypes.number,
};

export default UploadedFileIllustration;
