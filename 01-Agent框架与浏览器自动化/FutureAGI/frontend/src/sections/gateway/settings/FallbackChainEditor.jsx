/* eslint-disable react/prop-types */
import React from "react";
import {
  Stack,
  TextField,
  IconButton,
  Button,
  Card,
  CardContent,
  MenuItem,
} from "@mui/material";
import Iconify from "src/components/iconify";
import { useAvailableModels } from "../hooks/useAvailableModels";

const FallbackChainEditor = ({
  primaryModel,
  fallbacks,
  onChange,
  onRemoveChain,
  models: modelsProp,
}) => {
  const dynamicModels = useAvailableModels();
  const models = modelsProp || dynamicModels;
  const handlePrimaryChange = (e) => {
    onChange(e.target.value, fallbacks);
  };

  const handleFallbackChange = (index, value) => {
    const updated = [...fallbacks];
    updated[index] = value;
    onChange(primaryModel, updated);
  };

  const handleAddFallback = () => {
    onChange(primaryModel, [...fallbacks, ""]);
  };

  const handleRemoveFallback = (index) => {
    const updated = fallbacks.filter((_, i) => i !== index);
    onChange(primaryModel, updated);
  };

  return (
    <Card variant="outlined" sx={{ mb: 1 }}>
      <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
        <Stack direction="row" alignItems="center" spacing={1} flexWrap="wrap">
          <TextField
            select
            size="small"
            value={primaryModel}
            onChange={handlePrimaryChange}
            sx={{ minWidth: 160 }}
            label="Primary"
          >
            {models.map((m) => (
              <MenuItem key={m} value={m}>
                {m}
              </MenuItem>
            ))}
          </TextField>

          {fallbacks.map((fb, i) => (
            <React.Fragment key={i}>
              <Iconify
                icon="mdi:arrow-right"
                width={20}
                sx={{ color: "text.secondary" }}
              />
              <TextField
                select
                size="small"
                value={fb}
                onChange={(e) => handleFallbackChange(i, e.target.value)}
                sx={{ minWidth: 160 }}
                label={`Fallback ${i + 1}`}
              >
                {models.map((m) => (
                  <MenuItem key={m} value={m}>
                    {m}
                  </MenuItem>
                ))}
              </TextField>
              <IconButton size="small" onClick={() => handleRemoveFallback(i)}>
                <Iconify icon="mdi:close" width={16} />
              </IconButton>
            </React.Fragment>
          ))}

          <Button
            size="small"
            onClick={handleAddFallback}
            startIcon={<Iconify icon="mdi:plus" width={16} />}
          >
            Add
          </Button>

          {onRemoveChain && (
            <IconButton
              size="small"
              onClick={onRemoveChain}
              sx={{ ml: "auto" }}
            >
              <Iconify
                icon="mdi:delete-outline"
                width={18}
                color="error.main"
              />
            </IconButton>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

export default FallbackChainEditor;
