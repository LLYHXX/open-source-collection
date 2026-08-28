import {
  Box,
  Button,
  Card,
  Collapse,
  Container,
  Grid,
  IconButton,
  Paper,
  Select,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Typography,
  alpha,
} from "@mui/material";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { useSettingsContext } from "src/components/settings";
import WorstSlices from "./worst-slices";
import { m } from "framer-motion";
import { varHover } from "src/components/animate";
import Iconify from "src/components/iconify";
import { usePopover } from "src/components/custom-popover";
import OneDHeatmap from "src/components/charts/one-d-heatmap";
import Scrollbar from "src/components/scrollbar";
import { useBoolean } from "src/hooks/use-boolean";
import ColumnChart from "src/components/charts/column-chart";
import MultiLineChart from "src/components/charts/multi-line-chart";

export default function DataSlices() {
  const histogramPopover = usePopover();

  const settings = useSettingsContext();

  const [currentTab, setCurrentTab] = useState("features");

  function handleTab(event, newValue) {
    setCurrentTab(newValue);
  }

  const headerContent = (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        p: 1,
      }}
    >
      <Typography variant="h6">Predictions</Typography>
      <Button
        component={m.button}
        whileTap="tap"
        whileHover="hover"
        variants={varHover(1.05)}
        // startIcon={<Iconify icon="material-symbols:edit" />}
        onClick={histogramPopover.onOpen}
      >
        Sort Histogram
      </Button>
    </Box>
  );

  const tabs = (
    <Box>
      <Tabs
        value={currentTab}
        onChange={handleTab}
        sx={{
          px: 2.5,
          boxShadow: (theme) =>
            `inset 0 -2px 0 0 ${alpha(theme.palette.text.disabled, 0.08)}`,
        }}
      >
        <Tab value="features" label="Features" />
        <Tab value="tags" label="Tags" />
      </Tabs>
    </Box>
  );
  const quantileInfo = (
    <Box sx={{ p: 1 }}>
      <Grid container alignItems="center">
        <Grid item xs={3}>
          <Select></Select>
        </Grid>
        <Grid item xs={3}>
          Metric
        </Grid>
        <Grid item xs={6}>
          <OneDHeatmap></OneDHeatmap>
        </Grid>
      </Grid>
    </Box>
  );

  const detailsTable = (
    <Box>
      <TableContainer sx={{ mt: 3, overflow: "unset" }}>
        <Scrollbar>
          <Table sx={{ width: "100%" }} size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell />
                <TableCell>Feature Name</TableCell>
                <TableCell>Histogram</TableCell>
                <TableCell>Feature Importance</TableCell>
                <TableCell></TableCell>
              </TableRow>
            </TableHead>

            <TableBody key="main-table">
              <CollapsibleTableRow></CollapsibleTableRow>
            </TableBody>
          </Table>
        </Scrollbar>
      </TableContainer>
    </Box>
  );

  return (
    <Container maxWidth={settings.themeStretch ? false : "xl"}>
      <Stack component={Card} direction="row" sx={{ height: "85vh" }}>
        <WorstSlices></WorstSlices>

        <Stack
          sx={{
            width: 1,
            height: 1,
            overflow: "hidden",
          }}
        >
          {headerContent}

          {tabs}

          {quantileInfo}

          {detailsTable}
        </Stack>
      </Stack>
    </Container>
  );
}

DataSlices.propTypes = {
  model: PropTypes.object,
};

// ----------------------------------------------------------------------

function CollapsibleTableRow() {
  const collapsible = useBoolean();

  const [currentTab, setCurrentTab] = useState("sliceDistribution");

  function handleTab(event, newValue) {
    setCurrentTab(newValue);
  }

  return (
    <>
      <TableRow>
        <TableCell>
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
        </TableCell>

        <TableCell>Name</TableCell>

        <TableCell>
          <ColumnChart size="small"></ColumnChart>
        </TableCell>

        <TableCell>Value</TableCell>

        <TableCell>Link</TableCell>
      </TableRow>

      <TableRow>
        <TableCell sx={{ py: 0 }} colSpan={6}>
          <Collapse in={collapsible.value} unmountOnExit>
            <Paper
              variant="outlined"
              sx={{
                py: 2,
                borderRadius: 1.5,
                ...(collapsible.value && {
                  boxShadow: (theme) => theme.customShadows.z20,
                }),
              }}
            >
              <Tabs
                value={currentTab}
                onChange={handleTab}
                sx={{
                  px: 2.5,
                  boxShadow: (theme) =>
                    `inset 0 -2px 0 0 ${alpha(theme.palette.text.disabled, 0.08)}`,
                }}
              >
                <Tab value="sliceDistribution" label="Slice Distribution" />
                <Tab
                  value="performanceOverTime"
                  label="Slice Performance Over Time"
                />
              </Tabs>

              {currentTab === "sliceDistribution" && (
                <ColumnChart></ColumnChart>
              )}

              {currentTab === "performanceOverTime" && (
                <>
                  <Box
                    sx={{
                      display: "flex",
                      // justifyContent: "space-between",
                      alignItems: "center",
                      p: 1,
                    }}
                  >
                    <Typography>Showing _ out of _</Typography>
                    <Button
                      component={m.button}
                      whileTap="tap"
                      whileHover="hover"
                      variants={varHover(1.05)}
                      // startIcon={<Iconify icon="material-symbols:edit" />}
                      // onClick={histogramPopover.onOpen}
                    >
                      Slices
                    </Button>
                  </Box>
                  <MultiLineChart></MultiLineChart>
                </>
              )}
            </Paper>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

CollapsibleTableRow.propTypes = {
  row: PropTypes.object,
  propsToShow: PropTypes.array,
  idNum: PropTypes.number,
};
