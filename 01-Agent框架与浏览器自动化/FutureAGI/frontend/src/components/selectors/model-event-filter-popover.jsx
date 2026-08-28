import PropTypes from "prop-types";
import {
  Box,
  Button,
  Card,
  Divider,
  Drawer,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  List,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { m } from "framer-motion";
import React, { useEffect, useState } from "react";
import { useBoolean } from "src/hooks/use-boolean";
import Iconify from "../iconify";
import { varHover } from "../animate";
import Scrollbar from "../scrollbar";
import FeatureValueAutocomplete from "./feature-value-autocomplete";
import { emptyfilter } from "./helper";

export default function ModelEventFilterPopover({
  onFilterChange,
  filters,
  datasets,
  showComparisonDataset,
}) {
  const drawer = useBoolean();
  const [featureNames, setFeatureNames] = useState({
    feature: [],
    prediction: [],
    actual: [],
    tag: [],
  });

  useEffect(() => {
    const allFeatureNames = {
      feature: [],
      prediction: [],
      actual: [],
      tag: [],
    };
    if (datasets?.predictionLabel) {
      // eslint-disable-next-line
      for (const val of datasets?.predictionLabel) {
        allFeatureNames.prediction.push({
          name: val.name,
          dataType: val.dataType,
        });
      }
    }
    if (datasets?.actualLabel) {
      // eslint-disable-next-line
      for (const val of datasets?.actualLabel) {
        allFeatureNames.actual.push({
          name: val.name,
          dataType: val.dataType,
        });
      }
    }
    if (datasets?.categorical) {
      // eslint-disable-next-line
      for (const val of datasets?.categorical) {
        allFeatureNames.feature.push({
          name: val.name,
          dataType: val.dataType,
        });
      }
    }
    if (datasets?.numerical) {
      // eslint-disable-next-line
      for (const val of datasets?.numerical) {
        allFeatureNames.feature.push({
          name: val.name,
          dataType: val.dataType,
        });
      }
    }
    if (datasets?.tags) {
      // eslint-disable-next-line
      for (const val of datasets?.tags) {
        allFeatureNames.tags.push({
          name: val.name,
          dataType: val.dataType,
        });
      }
    }
    setFeatureNames(allFeatureNames);
  }, [datasets]);

  function addFilter() {
    const newFilter = [...filters, emptyfilter];
    onFilterChange(newFilter);
  }
  function removeFilter(filterIndex) {
    const newFilter = [...filters];
    if (filterIndex > -1) {
      // only splice array when item is found
      newFilter.splice(filterIndex, 1); // 2nd parameter means remove one item only
    }
    onFilterChange(newFilter);
  }

  function updateFilter(filterIndex, valueType, value) {
    const newFilter = [...filters];
    if (valueType == "featureName") {
      const v = value.split("::");
      newFilter[filterIndex]["featureName"] = v[0];
      newFilter[filterIndex]["dataType"] = v[1];
    } else if (valueType == "featureValue") {
      //
    } else {
      newFilter[filterIndex][valueType] = value;
    }
    onFilterChange(newFilter);
  }

  function onAutocompleteChange(newValue, filterIndex) {
    const newFilter = [...filters];
    newFilter[filterIndex]["filterValues"] = newValue;
    onFilterChange(newFilter);
  }

  const renderHead = (
    <Box alignItems="center" sx={{ py: 2, pl: 2.5, pr: 1, minHeight: 68 }}>
      <Typography variant="h6" sx={{ flexGrow: 1 }}>
        <IconButton onClick={addFilter}>
          <Iconify icon="material-symbols:add" />
        </IconButton>
        Filters
      </Typography>
      <Divider />
    </Box>
  );

  const filledFilters = filters.filter((x) => x.isFilled);

  return (
    <>
      <Button
        component={m.button}
        whileTap="tap"
        whileHover="hover"
        variants={varHover(1.05)}
        // color={drawer.value ? "primary" : "default"}
        onClick={drawer.onTrue}
        variant="outlined"
        startIcon={<Iconify icon="mdi:filter-outline" />}
        endIcon={<Iconify icon="mingcute:down-fill" />}
      >
        Filter {filledFilters.length > 0 && `by (${filledFilters.length})`}
      </Button>

      <Drawer
        open={drawer.value}
        onClose={drawer.onFalse}
        anchor="right"
        slotProps={{
          backdrop: { invisible: true },
        }}
        PaperProps={{
          sx: { width: 1, maxWidth: 600 },
        }}
      >
        {renderHead}

        <Scrollbar>
          <List disablePadding>
            {filters?.map((filter, filterIndex) => (
              <div key={filterIndex}>
                <Card sx={{ p: 1, m: 1 }}>
                  <Grid container alignItems="center" spacing={1}>
                    <Grid item xs={1}>
                      <IconButton
                        component={m.button}
                        whileTap="tap"
                        whileHover="hover"
                        variants={varHover(1.05)}
                        // color={drawer.value ? "primary" : "default"}
                        onClick={() => removeFilter(filterIndex)}
                      >
                        <Iconify icon="entypo:cross" width={24} />
                      </IconButton>
                    </Grid>

                    <Grid item xs={8}>
                      <Grid container>
                        <Grid item xs={12}>
                          <Stack direction="row" spacing={0}>
                            <FormControl size="small" sx={{ width: "33%" }}>
                              <InputLabel id="filter-dimension-label">
                                Type
                              </InputLabel>
                              <Select
                                labelId="filter-dimension-label"
                                id="filter-dimension"
                                value={filter.type}
                                label="Type"
                                // onChange={handleChange}
                                onChange={(val) =>
                                  updateFilter(
                                    filterIndex,
                                    "type",
                                    val.target.value,
                                  )
                                }
                              >
                                <MenuItem value={"feature"}>Feature</MenuItem>
                                <MenuItem value={"prediction"}>
                                  Prediction
                                </MenuItem>
                                <MenuItem value={"actual"}>Actual</MenuItem>
                                <MenuItem value={"tag"}>Tag</MenuItem>
                              </Select>
                            </FormControl>

                            <FormControl size="small" sx={{ width: "33%" }}>
                              <InputLabel id="property-select-label">
                                Property
                              </InputLabel>
                              <Select
                                labelId="property-select-label"
                                id="property-select"
                                value={`${filter.featureName}::${filter.dataType}`}
                                label="Property"
                                onChange={(val) =>
                                  updateFilter(
                                    filterIndex,
                                    "featureName",
                                    val.target.value,
                                  )
                                }
                              >
                                {featureNames[filter.type]?.map(
                                  (fName, fIndex) => (
                                    <MenuItem
                                      key={fIndex}
                                      value={`${fName.name}::${fName.dataType}`}
                                    >
                                      {fName.name}
                                    </MenuItem>
                                  ),
                                )}
                              </Select>
                            </FormControl>
                            <FormControl size="small" sx={{ width: "33%" }}>
                              <InputLabel id="comparison-fn-select-label">
                                Comparison
                              </InputLabel>
                              <Select
                                labelId="comparison-fn-label"
                                id="comparison-fn"
                                value={filter.comparisonFn}
                                label="Comparison"
                                onChange={(val) =>
                                  updateFilter(
                                    filterIndex,
                                    "comparisonFn",
                                    val.target.value,
                                  )
                                }
                              >
                                <MenuItem value={"equal"}>is equal to</MenuItem>
                                <MenuItem value={"notEqual"}>
                                  is not equal to
                                </MenuItem>
                                {filter.dataType === "number" && (
                                  <>
                                    <MenuItem value={"greater"}>
                                      is greater than
                                    </MenuItem>
                                    <MenuItem value={"greaterOrEqual"}>
                                      is greater than or equal to
                                    </MenuItem>
                                    <MenuItem value={"less"}>
                                      is less than
                                    </MenuItem>
                                    <MenuItem value={"lessOrEqual"}>
                                      is less than or equal to
                                    </MenuItem>
                                  </>
                                )}
                              </Select>
                            </FormControl>
                          </Stack>
                        </Grid>
                        <Grid item xs>
                          <FeatureValueAutocomplete
                            selectedValues={filter.filterValues}
                            index={filterIndex}
                            onChange={onAutocompleteChange}
                          ></FeatureValueAutocomplete>
                        </Grid>
                      </Grid>
                    </Grid>

                    <Grid item xs={3}>
                      <FormControl size="small" sx={{ width: "100%" }}>
                        <InputLabel id="dataset-label">Age</InputLabel>
                        <Select
                          labelId="dataset-label"
                          id="dataset"
                          value={"primary"}
                          label="Dataset"
                          // onChange={handleChange}
                        >
                          <MenuItem value={"primary"}>Primary</MenuItem>
                          {showComparisonDataset && (
                            <MenuItem value={"comparison"}>Comparison</MenuItem>
                          )}
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>
                </Card>
              </div>
            ))}
          </List>
        </Scrollbar>
      </Drawer>
    </>
  );
}

ModelEventFilterPopover.propTypes = {
  onFilterChange: PropTypes.func,
  filters: PropTypes.array,
  datasets: PropTypes.object,
  showComparisonDataset: PropTypes.bool,
};
