import { Box } from "@mui/material";
import "./loader.css";

const Loader = () => {
  return (
    <Box className="loader-container">
      <Box className="loader">
        {[...Array(8)].map((_, index) => (
          <Box
            key={index}
            className="loader-dot"
            sx={{
              transform: `rotate(${index * 45}deg) translateY(-20px)`,
              animationDelay: `${index * 0.15}s`,
            }}
          />
        ))}
      </Box>
    </Box>
  );
};

export default Loader;
