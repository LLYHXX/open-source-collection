import { Box, Button, Card } from "@mui/material";
import React from "react";
import Iconify from "src/components/iconify";

const DatasetFilterCard = () => {
  return (
    <Card sx={{ padding: 2, border: "none", display: "flex" }}>
      <Box sx={{ flex: 1 }} />
      <Box>
        <Button
          variant="contained"
          color="primary"
          onClick={() => {}}
          startIcon={<Iconify icon="ic:round-plus" />}
          sx={{
            "& .MuiButton-startIcon": {
              margin: 0,
            },
          }}
        />
      </Box>
    </Card>
  );
};

export default DatasetFilterCard;
