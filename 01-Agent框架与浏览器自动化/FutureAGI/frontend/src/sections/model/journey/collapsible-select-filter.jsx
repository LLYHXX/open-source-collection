import {
  Button,
  Card,
  CardHeader,
  Collapse,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
} from "@mui/material";
import PropTypes from "prop-types";
import React, { useState } from "react";
import Iconify from "src/components/iconify";
import { useBoolean } from "src/hooks/use-boolean";

const filterSkeleton = {
  propertyType: null,
  propertyName: null,
  equalityCondition: null,
  values: null,
  isFilled: false,
};

export default function CollapsibleSelectFilter() {
  const collapsible = useBoolean();

  const [eventFilters, onChangeEventFilters] = useState([]);

  function onAddEvent() {
    if (eventFilters.length == 0) {
      onChangeEventFilters([filterSkeleton]);
    } else {
      if (eventFilters[eventFilters.length - 1].isFilled) {
        onChangeEventFilters((prevValue) => [...prevValue, filterSkeleton]);
      }
    }
  }

  return (
    <Card
      sx={{
        p: 0,
      }}
      variant="outlined"
    >
      <CardHeader
        sx={{
          p: 1,
        }}
        title="Select Filter"
        action={
          <IconButton
            size="small"
            color={collapsible.value ? "inherit" : "default"}
            onClick={collapsible.onToggle}
          >
            <Iconify
              icon={
                collapsible.value
                  ? "eva:arrow-ios-upward-fill"
                  : "eva:arrow-ios-downward-fill"
              }
            />
          </IconButton>
        }
      />

      <Collapse in={collapsible.value} unmountOnExit>
        <Grid container sx={{ p: 2 }} spacing={2}>
          {eventFilters?.map((event, eventIndex) => (
            <>
              <Grid item xs={12} key={`body${eventIndex}`}>
                <Stack direction={"column"} spacing={1}>
                  <Stack direction={"row"} spacing={1}>
                    <FormControl sx={{ minWidth: 150 }} size="small">
                      <InputLabel>Property type</InputLabel>
                      <Select
                        // value={age}
                        label="Event Name"
                        // onChange={handleChange}
                        autoWidth
                      >
                        <MenuItem value={10}>Ten</MenuItem>
                        <MenuItem value={20}>Twenty</MenuItem>
                        <MenuItem value={30}>Thirty</MenuItem>
                      </Select>
                    </FormControl>

                    <FormControl sx={{ minWidth: 150 }} size="small">
                      <InputLabel>Event Name</InputLabel>
                      <Select
                        // value={age}
                        label="Event Name"
                        // onChange={handleChange}
                        autoWidth
                      >
                        <MenuItem value={10}>Ten</MenuItem>
                        <MenuItem value={20}>Twenty</MenuItem>
                        <MenuItem value={30}>Thirty</MenuItem>
                      </Select>
                    </FormControl>

                    <FormControl sx={{ minWidth: 150 }} size="small">
                      <InputLabel>Event Name</InputLabel>
                      <Select
                        // value={age}
                        label="Event Name"
                        // onChange={handleChange}
                        autoWidth
                      >
                        <MenuItem value={10}>Ten</MenuItem>
                        <MenuItem value={20}>Twenty</MenuItem>
                        <MenuItem value={30}>Thirty</MenuItem>
                      </Select>
                    </FormControl>

                    <FormControl sx={{ minWidth: 150 }} size="small">
                      <InputLabel>Event Name</InputLabel>
                      <Select
                        // value={age}
                        label="Event Name"
                        // onChange={handleChange}
                        autoWidth
                      >
                        <MenuItem value={10}>Ten</MenuItem>
                        <MenuItem value={20}>Twenty</MenuItem>
                        <MenuItem value={30}>Thirty</MenuItem>
                      </Select>
                    </FormControl>

                    <FormControl sx={{ minWidth: 150 }} size="small">
                      <InputLabel>Event Name</InputLabel>
                      <Select
                        // value={age}
                        label="Event Name"
                        // onChange={handleChange}
                        autoWidth
                      >
                        <MenuItem value={10}>Ten</MenuItem>
                        <MenuItem value={20}>Twenty</MenuItem>
                        <MenuItem value={30}>Thirty</MenuItem>
                      </Select>
                    </FormControl>

                    <IconButton>
                      <Iconify icon={"material-symbols:delete"} />
                    </IconButton>
                  </Stack>
                </Stack>
              </Grid>
            </>
          ))}

          <Grid item xs={12}>
            <Button
              // sx={{ width: 120 }}
              variant="outlined"
              startIcon={<Iconify icon="material-symbols:add" />}
              onClick={onAddEvent}
            >
              Add Event
            </Button>
          </Grid>
        </Grid>
      </Collapse>
    </Card>
  );
}

CollapsibleSelectFilter.propTypes = {
  // eventFilters: PropTypes.array,
  onEventFiltersChange: PropTypes.func,
};
