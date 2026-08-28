import {
  Box,
  Checkbox,
  Divider,
  FormControl,
  FormControlLabel,
  FormGroup,
  InputLabel,
  Select,
} from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import Scrollbar from "src/components/scrollbar";

export default function ClusterViewSettings() {
  const [checked, setChecked] = React.useState([true, false]);

  const handleChange1 = (event) => {
    setChecked([event.target.checked, event.target.checked]);
  };

  const handleChange2 = (event) => {
    setChecked([event.target.checked, checked[1]]);
  };

  const handleChange3 = (event) => {
    setChecked([checked[0], event.target.checked]);
  };

  const children = (
    <Box sx={{ display: "flex", flexDirection: "column", ml: 3 }}>
      <FormControlLabel
        label="Child 1"
        control={<Checkbox checked={checked[0]} onChange={handleChange2} />}
      />
      <FormControlLabel
        label="Child 2"
        control={<Checkbox checked={checked[1]} onChange={handleChange3} />}
      />
    </Box>
  );

  return (
    <>
      <Box>
        <Scrollbar>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="color-type-label">Color By</InputLabel>
            <Select
              labelId="color-type-label"
              id="color-type-select"
              // value={
              //   datasetSelection?.environment
              //     ? datasetSelection?.environment
              //     : "-"
              // }
              label="Color By"
              // onChange={(e) => handleChange(e, "environment")}
            >
              {/* {datasets?.environments?.map((row, index) => (
                <MenuItem key={index} value={row?.environment}>
                  {row?.environment}
                </MenuItem>
              ))} */}
              {/* <MenuItem key="" value="Production">Production</MenuItem> */}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="val-label">Environment</InputLabel>
            <Select
              labelId="val-label"
              id="val-select"
              // value={
              //   datasetSelection?.environment
              //     ? datasetSelection?.environment
              //     : "-"
              // }
              // onChange={(e) => handleChange(e, "environment")}
            >
              {/* {datasets?.environments?.map((row, index) => (
                <MenuItem key={index} value={row?.environment}>
                  {row?.environment}
                </MenuItem>
              ))} */}
              {/* <MenuItem key="" value="Production">Production</MenuItem> */}
            </Select>
          </FormControl>

          <Divider></Divider>

          <FormGroup>
            <FormControlLabel
              control={<Checkbox defaultChecked />}
              label="Label"
            />
            <FormControlLabel
              control={<Checkbox defaultChecked />}
              label="Required"
            />
          </FormGroup>
          <FormControlLabel
            label="Select Al"
            control={
              <Checkbox
                checked={checked[0] && checked[1]}
                indeterminate={checked[0] !== checked[1]}
                onChange={handleChange1}
              />
            }
          />
          {children}
        </Scrollbar>
      </Box>
    </>
  );
}

ClusterViewSettings.propTypes = {
  colorby: PropTypes.string,
  onColorBychange: PropTypes.func,
  clusterData: PropTypes.object,
};
