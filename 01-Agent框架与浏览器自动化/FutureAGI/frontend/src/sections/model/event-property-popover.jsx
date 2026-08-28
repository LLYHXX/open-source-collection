import PropTypes from "prop-types";
import {
  Button,
  Checkbox,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  TextField,
} from "@mui/material";
import React, { useMemo, useState } from "react";

export default function EventPropertyPopover({
  properties,
  onPropertiesSelectionChange,
}) {
  const [searchTerm, setSearchTerm] = useState("");

  function handleToggle(index) {
    if (index === -1) {
      const updatedProperties = properties.map((prop) => {
        // Change the 'selected' state of the property that was toggled
        if (prop.selected && !prop.disabled) {
          return { ...prop, selected: false };
        }
        return prop;
      });
      onPropertiesSelectionChange(updatedProperties);
    } else {
      const updatedProperties = properties.map((prop, i) => {
        // Change the 'selected' state of the property that was toggled
        if (i === index) {
          return { ...prop, selected: !prop.selected };
        }
        return prop;
      });
      onPropertiesSelectionChange(updatedProperties);
    }
  }

  const filteredProperties = useMemo(() => {
    return properties?.filter((property) =>
      property.name.toLowerCase().includes(searchTerm.toLowerCase()),
    );
  }, [properties, searchTerm]);

  const handleSearchChange = (property) => {
    setSearchTerm(property.target.value);
  };

  return (
    <>
      <TextField label="Search Events" onChange={handleSearchChange} />
      <List
        sx={{
          width: "100%",
          maxWidth: 360,
          bgcolor: "background.paper",
          maxHeight: 300,
          overflow: "auto",
        }}
      >
        <ListItem key="deselect-listitem" disablePadding>
          <ListItemButton
            disabled={
              properties?.filter((value) => value.selected).length ===
              properties?.filter((value) => value.disabled).length
            }
            role={undefined}
            onClick={() => handleToggle(-1)}
            dense
          >
            <ListItemIcon>
              <Checkbox
                edge="start"
                tabIndex={-1}
                disableRipple
                inputProps={{ "aria-labelledby": "deselect-listitem" }}
                indeterminate={true}
              />
            </ListItemIcon>
            <ListItemText
              id={`checkbox-list-label-deselect-listitem`}
              primary={"Deselect All"}
            />
          </ListItemButton>
        </ListItem>
        {filteredProperties?.map((value) => {
          const labelId = `checkbox-list-label-${value.name}`;
          return (
            <ListItem key={value.name} disablePadding>
              <ListItemButton
                disabled={value.disabled}
                role={undefined}
                onClick={() => handleToggle(value.index)}
                dense
              >
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={value.selected}
                    tabIndex={-1}
                    disableRipple
                    inputProps={{ "aria-labelledby": labelId }}
                  />
                </ListItemIcon>
                <ListItemText id={labelId} primary={value.name} />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
      <Button>
        Select | {properties?.filter((value) => value.selected).length}
      </Button>
    </>
  );
}

EventPropertyPopover.propTypes = {
  selectedProperties: PropTypes.array,
  properties: PropTypes.array,
  onPropertiesSelectionChange: PropTypes.func,
};
