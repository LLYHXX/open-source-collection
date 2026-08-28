import PropTypes from "prop-types";
import {
  Box,
  Card,
  Chip,
  IconButton,
  InputAdornment,
  TextField,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import Iconify from "src/components/iconify";
import { enqueueSnackbar } from "notistack";

ConnectionInfo.propTypes = {
  config: PropTypes.object,
};

export default function ConnectionInfo({ config }) {
  const theme = useTheme();

  const mcpUrl = config?.mcp_url || "";

  const handleCopy = (text, label) => {
    navigator.clipboard.writeText(text).then(() => {
      enqueueSnackbar(`${label} copied to clipboard`, { variant: "success" });
    });
  };

  return (
    <Card variant="outlined" sx={{ p: theme.spacing(3), mb: theme.spacing(3) }}>
      <Typography
        sx={{
          typography: "m2",
          fontWeight: "fontWeightSemiBold",
          color: "text.primary",
          mb: theme.spacing(2),
        }}
      >
        Connection Details
      </Typography>
      <Typography
        sx={{
          typography: "s1",
          color: "text.secondary",
          mb: theme.spacing(3),
        }}
      >
        Your MCP endpoint URL. Authentication is handled via OAuth — your IDE
        will prompt you to log in on first connection.
      </Typography>

      <Box
        display="flex"
        flexDirection="column"
        gap={theme.spacing(2)}
        maxWidth={560}
      >
        <TextField
          label="MCP Endpoint URL"
          value={mcpUrl}
          fullWidth
          size="small"
          InputProps={{
            readOnly: true,
            endAdornment: (
              <InputAdornment position="end">
                <Tooltip title="Copy URL">
                  <IconButton
                    size="small"
                    onClick={() => handleCopy(mcpUrl, "MCP URL")}
                  >
                    <Iconify icon="ph:copy" width={18} />
                  </IconButton>
                </Tooltip>
              </InputAdornment>
            ),
          }}
        />

        <Box display="flex" alignItems="center" gap={1}>
          <Iconify
            icon="ph:shield-check"
            width={18}
            sx={{ color: "success.main" }}
          />
          <Typography sx={{ typography: "s2", color: "text.secondary" }}>
            Authentication: OAuth 2.0
          </Typography>
          <Chip label="Secure" size="small" color="success" variant="soft" />
        </Box>
      </Box>
    </Card>
  );
}
