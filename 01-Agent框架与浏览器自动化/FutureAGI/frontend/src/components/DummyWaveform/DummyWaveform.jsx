import { Box, Stack } from "@mui/material";
import PropTypes from "prop-types";
import React, { useEffect, useRef, useState } from "react";

function Bar({ height }) {
  return (
    <Box
      sx={{
        height: `${height}px`,
        width: "2px",
        bgcolor: "action.hover",
        flexShrink: 0,
      }}
    />
  );
}

Bar.propTypes = {
  height: PropTypes.number,
};

export default function DummyWaveform() {
  const containerRef = useRef(null);
  const [heights, setHeights] = useState([]);

  useEffect(() => {
    if (!containerRef.current) return;

    const barWidth = 2;
    const gap = 2.8; // 0.35 = 2.8px

    const observer = new ResizeObserver(() => {
      const width = containerRef.current?.offsetWidth ?? 100;
      const count = Math.floor(width / (barWidth + gap));

      setHeights(
        Array.from(
          { length: count },
          () => Math.floor(Math.random() * (15 - 4 + 1)) + 4,
        ),
      );
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <Stack
      ref={containerRef}
      direction="row"
      alignItems="center"
      gap={0.35}
      sx={{ width: "100%" }}
    >
      {heights.map((h, index) => (
        <Bar key={index} height={h} />
      ))}
    </Stack>
  );
}
