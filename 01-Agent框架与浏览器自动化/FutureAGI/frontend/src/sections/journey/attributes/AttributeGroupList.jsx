import { useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  List,
  ListItemButton,
  ListItemText,
  TextField,
  InputAdornment,
} from "@mui/material";
import Iconify from "src/components/iconify";

const AttributeGroupList = ({ groups, selectedGroup, onSelectGroup }) => {
  const [search, setSearch] = useState("");

  const filtered = groups.filter((g) =>
    g.prefix.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <Box
      sx={{
        width: 220,
        borderRight: 1,
        borderColor: "divider",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box sx={{ p: 1.5, borderBottom: 1, borderColor: "divider" }}>
        <TextField
          size="small"
          fullWidth
          placeholder="Search groups..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Iconify
                  icon="eva:search-fill"
                  width={16}
                  sx={{ color: "text.disabled" }}
                />
              </InputAdornment>
            ),
          }}
        />
      </Box>
      <Box sx={{ p: 1, borderBottom: 1, borderColor: "divider" }}>
        <ListItemButton
          selected={selectedGroup === null}
          onClick={() => onSelectGroup(null)}
          sx={{ borderRadius: 1, py: 0.5 }}
        >
          <ListItemText
            primary="All"
            primaryTypographyProps={{
              variant: "body2",
              fontWeight: selectedGroup === null ? 600 : 400,
            }}
          />
        </ListItemButton>
      </Box>
      <List sx={{ overflow: "auto", flex: 1, p: 1 }} dense>
        {filtered.map((group) => (
          <ListItemButton
            key={group.prefix}
            selected={selectedGroup === group.prefix}
            onClick={() => onSelectGroup(group.prefix)}
            sx={{ borderRadius: 1, py: 0.5 }}
          >
            <ListItemText
              primary={`${group.prefix}.*`}
              secondary={`${group.keys.length} keys`}
              primaryTypographyProps={{
                variant: "body2",
                fontWeight: selectedGroup === group.prefix ? 600 : 400,
                noWrap: true,
              }}
              secondaryTypographyProps={{ variant: "caption" }}
            />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
};

AttributeGroupList.propTypes = {
  groups: PropTypes.arrayOf(
    PropTypes.shape({
      prefix: PropTypes.string,
      keys: PropTypes.array,
    }),
  ).isRequired,
  selectedGroup: PropTypes.string,
  onSelectGroup: PropTypes.func.isRequired,
};

export default AttributeGroupList;
