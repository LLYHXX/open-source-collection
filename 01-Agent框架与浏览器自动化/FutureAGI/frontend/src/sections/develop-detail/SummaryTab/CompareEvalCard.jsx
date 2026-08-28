import React, { useState, useEffect, useMemo } from "react";
import {
  Box,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import PropTypes from "prop-types";
import { useMutation } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { colorPalette } from "src/utils/utils";
import CompareEvalTable from "./CompareEvalTable";
import CompareEvalCharts from "./CompareEvalCharts";

const CompareEvalCardSkeleton = () => {
  return (
    <Box sx={{ width: "100%", padding: "16px" }}>
      {/* Table Skeleton */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              {[1, 2, 3, 4].map((col) => (
                <TableCell key={col}>
                  <Skeleton variant="text" width={100} />
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {[1, 2, 3, 4].map((row) => (
              <TableRow key={row}>
                {[1, 2, 3, 4].map((col) => (
                  <TableCell key={col}>
                    <Skeleton variant="text" width={80} />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Charts Skeleton */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          mt: 3,
          width: "100%",
        }}
      >
        <Box sx={{ width: "100%" }}>
          <Skeleton variant="text" width="25%" height={40} />
          <Skeleton variant="rectangular" width="100%" height={200} />
        </Box>
      </Box>
    </Box>
  );
};

const CompareEvalCard = ({
  baseColumn,
  selectedDatasets,
  setEvalsData,
  commonColumn,
  dataAfterChooseWinner,
  isChooseWinnerSelected,
  setIsChooseWinnerButtonVisible,
  isCommonColumn,
}) => {
  const [tableData, setTableData] = useState([]);
  const [columnConfig, setColumnConfig] = useState([]);
  const [multiChartData, setMultiChartData] = useState({});
  const [isWinnerChosen, setIsWinnerChosen] = useState(false);
  const [hasRankColumn, setHasRankColumn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [rowCount, setRowCount] = useState(0);

  const getSummaryTableData = (response) => {
    if (response?.data?.result) {
      setEvalsData(
        (response?.data?.result?.columnConfig || []).filter(
          (col) => col.name !== "rank",
        ),
      );

      const {
        table: rawTableData,
        columnConfig: rawColumnConfig,
        metadata,
      } = response.data.result;

      setIsWinnerChosen(metadata?.isWinnerChosen || false);

      const rankColumnExists = rawColumnConfig.some(
        (col) => col.name === "rank",
      );
      setHasRankColumn(rankColumnExists);

      const processedTableData = processTableData(
        rawTableData,
        rawColumnConfig,
      );

      setTableData(processedTableData);

      const filteredColumnConfig = rawColumnConfig.filter(
        (col) => col.name !== "rank",
      );
      setColumnConfig(filteredColumnConfig || []);

      const chartDataByColumn = createChartData(
        processedTableData,
        filteredColumnConfig,
      );
      setMultiChartData(chartDataByColumn);

      setIsLoading(false);
    }
  };

  const { mutate: getSummaryTable } = useMutation({
    mutationFn: () => {
      setIsLoading(true);
      return axios.post(
        endpoints.dataset.getSummaryTable(selectedDatasets[0]),
        {
          dataset_ids: selectedDatasets.slice(1),
          common_column_names: commonColumn,
          base_column_name: baseColumn,
        },
      );
    },
    onSuccess: (response) => {
      getSummaryTableData(response);
      setRowCount(response?.data?.result?.total_rows);
      setIsChooseWinnerButtonVisible(true);
    },
    onError: () => {
      setIsLoading(false);
      setIsChooseWinnerButtonVisible(false);
    },
  });

  const getSummaryDataFromIsChooseWinner = () => {
    if (dataAfterChooseWinner?.data?.result) {
      setEvalsData(
        (dataAfterChooseWinner?.data?.result?.columnConfig || []).filter(
          (col) => col.name !== "rank",
        ),
      );

      const {
        table: rawTableData,
        columnConfig: rawColumnConfig,
        metadata,
      } = dataAfterChooseWinner.data.result;

      setIsWinnerChosen(metadata?.isWinnerChosen || false);

      const rankColumnExists = rawColumnConfig.some(
        (col) => col.name === "rank",
      );
      setHasRankColumn(rankColumnExists);

      const processedTableData = processTableData(
        rawTableData,
        rawColumnConfig,
      );

      setTableData(processedTableData);

      const filteredColumnConfig = rawColumnConfig.filter(
        (col) => col.name !== "rank",
      );
      setColumnConfig(filteredColumnConfig || []);

      const chartDataByColumn = createChartData(
        processedTableData,
        filteredColumnConfig,
      );
      setMultiChartData(chartDataByColumn);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isChooseWinnerSelected) {
      getSummaryDataFromIsChooseWinner();
    } else {
      if (selectedDatasets.length > 1 && isCommonColumn) getSummaryTable();
    }
  }, [selectedDatasets, getSummaryTable, isChooseWinnerSelected]);

  const processTableData = (rawTableData) => {
    const datasetMap = new Map();

    // Extract unique dataset IDs
    const uniqueDatasetIds = [
      ...new Set(rawTableData.map((item) => item.datasetId)),
    ];

    // Initialize dataset objects
    uniqueDatasetIds.forEach((datasetId) => {
      const datasetEntry = rawTableData.find(
        (item) => item.datasetId === datasetId,
      );
      datasetMap.set(datasetId, {
        datasetId: datasetId,
        datasetName: datasetEntry.datasetName,
        rank: null, // Initialize rank as null
      });
    });

    // Fill in the metric values and rank for each dataset
    rawTableData.forEach((item) => {
      const dataset = datasetMap.get(item.datasetId);
      if (dataset) {
        // Use the columnName as the key and average as the value
        dataset[item.columnName] = item.average;

        // Set rank value if available in the API response
        if (item.rank !== undefined && item.rank !== null) {
          dataset.rank = item.rank;
        }
      }
    });

    // Convert the Map back to an array
    const processedTableData = Array.from(datasetMap.values());

    // Sort by rank if it exists
    if (
      isWinnerChosen &&
      processedTableData.some((item) => item.rank !== null)
    ) {
      processedTableData.sort((a, b) => (a.rank || 999) - (b.rank || 999));
    }

    return processedTableData;
  };

  // Create chart data for each metric
  const createChartData = (processedTableData, columnConfig) => {
    const chartDataByColumn = {};

    // Get metric columns from the column config
    const metricColumns = columnConfig.map((col) => col.name);

    // For each metric column, create chart data
    metricColumns.forEach((colName) => {
      // Only create chart data if some rows have this metric
      const rowsWithMetric = processedTableData.filter(
        (item) => item[colName] !== undefined && item[colName] !== null,
      );

      if (rowsWithMetric.length > 0) {
        chartDataByColumn[colName] = processedTableData
          // .filter(item => item[colName] !== undefined && item[colName] !== null)
          .map((item, index) => {
            return {
              id: item.datasetId.slice(0, 6),
              name: item.datasetName,
              value: parseFloat(item[colName]) || 0,
              fill: colorPalette[index % colorPalette.length].bgColor,
              textColor: colorPalette[index % colorPalette.length].textColor,
              rank: item.rank,
            };
          });
        // chartDataByColumn[colName].sort((a, b) => b.value - a.value);
      }
    });

    return chartDataByColumn;
  };

  const metricColumns = useMemo(() => {
    return columnConfig.map((col) => col.name);
  }, [columnConfig]);

  // Return skeleton when loading
  if (isLoading) {
    return <CompareEvalCardSkeleton />;
  }

  return (
    <Box
      sx={{ width: "100%", overflowX: "auto", padding: "16px", height: "83vh" }}
    >
      {/* Table Component */}
      <CompareEvalTable
        tableData={tableData}
        columnConfig={columnConfig}
        hasRankColumn={hasRankColumn}
        rowCount={rowCount}
      />

      {/* Charts Component */}
      {metricColumns.length > 0 && (
        <CompareEvalCharts
          multiChartData={multiChartData}
          metricColumns={metricColumns}
        />
      )}
    </Box>
  );
};

// Prop validation remains the same
CompareEvalCard.propTypes = {
  setDataAfterChooseWinner: PropTypes.func,
  dataAfterChooseWinner: PropTypes.object,
  isChooseWinnerSelected: PropTypes.bool,
  datasetInfo: PropTypes.array,
  commonColumn: PropTypes.array,
  setEvalsData: PropTypes.func,
  baseColumn: PropTypes.string.isRequired,
  selectedDatasets: PropTypes.arrayOf(PropTypes.string).isRequired,
  setIsChooseWinnerButtonVisible: PropTypes.func,
  isCommonColumn: PropTypes.bool,
};

export default CompareEvalCard;
