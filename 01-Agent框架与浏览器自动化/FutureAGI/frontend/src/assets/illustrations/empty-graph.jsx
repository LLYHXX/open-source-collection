import React from "react";
import { useTheme } from "@mui/material/styles";

const EmptyGraph = () => {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";

  const BG_BLOB = isDark ? "#27272a" : "#F2F2F2";
  const PAPER = isDark ? "#18181b" : "white";
  const STROKE = isDark ? "#52525b" : "#BABABA";
  const BAR = isDark ? "#3f3f46" : "#D2D2D2";
  const DOT = isDark ? "#3f3f46" : "#CFCFCF";
  const GRID_LINE = isDark ? "#27272a" : "#F2F2F2";
  const X_MARK = isDark ? "#18181b" : "white";

  return (
    <svg
      width="134"
      height="110"
      viewBox="0 0 134 110"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M90.3694 41.4101C80.9443 41.4101 71.3613 41.0801 62.387 38.8601C53.4128 36.6401 45.5435 32.4901 38.2942 27.6301C33.5816 24.4601 29.2749 21.9501 23.1643 22.3301C17.1746 22.6104 11.4462 24.5951 6.82813 27.9901C-0.962298 33.9901 0.221485 45.2201 3.33314 53.0901C8.01191 64.9401 22.2286 73.1701 34.3708 78.5401C48.362 84.7401 63.6836 88.3401 79.1404 90.4101C92.6694 92.2301 109.998 93.5501 121.7 85.7301C132.456 78.5401 135.41 62.1301 132.771 51.0401C132.116 47.7827 130.149 44.8473 127.236 42.7801C119.693 37.8901 108.419 41.1601 99.9412 41.3201C96.7844 41.3301 93.5826 41.4001 90.3694 41.4101Z"
        fill={BG_BLOB}
      />
      <path
        d="M116.513 12H19.0254C16.2359 12 13.9746 14.0058 13.9746 16.48V78.33C13.9746 80.8042 16.2359 82.81 19.0254 82.81H116.513C119.302 82.81 121.564 80.8042 121.564 78.33V16.48C121.564 14.0058 119.302 12 116.513 12Z"
        fill={PAPER}
        stroke={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M17.9785 76.2197H114.226"
        stroke={GRID_LINE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M17.9785 65.02H114.226"
        stroke={GRID_LINE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M17.9785 53.8301H114.226"
        stroke={GRID_LINE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M17.9785 42.6299H114.226"
        stroke={GRID_LINE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M17.9785 31.4302H114.226"
        stroke={GRID_LINE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M17.9785 20.23H114.226"
        stroke={GRID_LINE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M36.8185 27.52H30.4824C28.9507 27.52 27.709 28.6214 27.709 29.98V74.36C27.709 75.7186 28.9507 76.82 30.4824 76.82H36.8185C38.3502 76.82 39.5919 75.7186 39.5919 74.36V29.98C39.5919 28.6214 38.3502 27.52 36.8185 27.52Z"
        fill={BAR}
      />
      <path
        d="M59.5685 46.75H53.2324C51.7007 46.75 50.459 47.8514 50.459 49.21V74.36C50.459 75.7186 51.7007 76.82 53.2324 76.82H59.5685C61.1002 76.82 62.3419 75.7186 62.3419 74.36V49.21C62.3419 47.8514 61.1002 46.75 59.5685 46.75Z"
        fill={BAR}
      />
      <path
        d="M82.3087 32.6802H75.9727C74.4409 32.6802 73.1992 33.7816 73.1992 35.1402V74.3502C73.1992 75.7088 74.4409 76.8102 75.9727 76.8102H82.3087C83.8404 76.8102 85.0822 75.7088 85.0822 74.3502V35.1402C85.0822 33.7816 83.8404 32.6802 82.3087 32.6802Z"
        fill={BAR}
      />
      <path
        d="M105.049 53.6299H98.7129C97.1812 53.6299 95.9395 54.7313 95.9395 56.0899V74.3499C95.9395 75.7085 97.1812 76.8099 98.7129 76.8099H105.049C106.581 76.8099 107.822 75.7085 107.822 74.3499V56.0899C107.822 54.7313 106.581 53.6299 105.049 53.6299Z"
        fill={BAR}
      />
      <path
        d="M28.2715 49.6799L34.8781 49.4499L53.379 66.3199L71.0794 52.0199L90.3694 57.6499L108.983 47.1099"
        stroke={STROKE}
        strokeWidth="1.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M40.6953 88.48V92.78"
        stroke={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M38.2715 90.6299H43.1194"
        stroke={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M127.404 31.8901V36.1901"
        stroke={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M124.98 34.04H129.828"
        stroke={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M5.74609 11.0601V15.3501"
        stroke={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M3.32227 13.21H8.17014"
        stroke={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M7.78651 69.71C8.39671 69.71 8.89137 69.2712 8.89137 68.73C8.89137 68.1888 8.39671 67.75 7.78651 67.75C7.17631 67.75 6.68164 68.1888 6.68164 68.73C6.68164 69.2712 7.17631 69.71 7.78651 69.71Z"
        fill={DOT}
      />
      <path
        d="M60.6849 1.96C61.2951 1.96 61.7898 1.52124 61.7898 0.980001C61.7898 0.438762 61.2951 0 60.6849 0C60.0747 0 59.5801 0.438762 59.5801 0.980001C59.5801 1.52124 60.0747 1.96 60.6849 1.96Z"
        fill={DOT}
      />
      <path
        d="M72.0384 109.82C94.8587 109.82 113.358 108.799 113.358 107.54C113.358 106.281 94.8587 105.26 72.0384 105.26C49.2182 105.26 30.7188 106.281 30.7188 107.54C30.7188 108.799 49.2182 109.82 72.0384 109.82Z"
        fill={BG_BLOB}
      />
      <path
        d="M117.562 24.6702C124.791 24.6702 130.651 19.4722 130.651 13.0602C130.651 6.64817 124.791 1.4502 117.562 1.4502C110.333 1.4502 104.473 6.64817 104.473 13.0602C104.473 19.4722 110.333 24.6702 117.562 24.6702Z"
        fill={BAR}
      />
      <path
        d="M111.869 8.00977L123.245 18.1098"
        stroke={X_MARK}
        strokeWidth="1.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M123.245 8.00977L111.869 18.1098"
        stroke={X_MARK}
        strokeWidth="1.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export default EmptyGraph;
