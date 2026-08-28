import React from "react";
import { FormControl, MenuItem, Select } from "@mui/material";

export default function InsightsGraphProps() {
  return (
    <>
      <FormControl
        sx={{
          width: 100,
        }}
        size="small"
      >
        {/* <InputLabel >Graph</InputLabel> */}
        <Select
          value={10}
          // label="Graph"
          // onChange={handleChange}
        >
          <MenuItem value={10}>Ten</MenuItem>
          <MenuItem value={20}>Twenty</MenuItem>
          <MenuItem value={30}>Thirty</MenuItem>
        </Select>
      </FormControl>
      <FormControl
        sx={{
          width: 100,
        }}
        size="small"
      >
        {/* <InputLabel >Graph</InputLabel> */}
        <Select
          value={10}
          // label="Graph"
          // onChange={handleChange}
        >
          <MenuItem value={10}>Ten</MenuItem>
          <MenuItem value={20}>Twenty</MenuItem>
          <MenuItem value={30}>Thirty</MenuItem>
        </Select>
      </FormControl>
    </>
  );
}
