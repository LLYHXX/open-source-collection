import {
  Box,
  CircularProgress,
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { format } from "date-fns";
import React, { useMemo } from "react";
import PropTypes from "prop-types";
import SecondaryCheckbox from "src/components/secondary-checkbox/SecondaryCheckbox";
import { useScrollEnd } from "src/hooks/use-scroll-end";
import { useNavigate } from "react-router";
import { useParams } from "src/routes/hooks";
import CustomTooltip from "src/components/tooltip/CustomTooltip";
import CustomTableCell from "src/components/table/custom-table-cell";

const DatasetTable = ({
  datasetData,
  fetchNextPage,
  isLoading,
  isFetchingNextPage,
  columns,
  datasetSelectMode,
  selectedDataset,
  setSelectedDataset,
  allSelectedDataset,
  setAllSelectedDataset,
  totalCount,
}) => {
  const scrollContainerRef = useScrollEnd(() => {
    if (isFetchingNextPage || isLoading) {
      return;
    }
    fetchNextPage();
  }, [isFetchingNextPage, isLoading]);

  const enabledColumns = columns?.filter((col) => col?.enabled);

  const navigate = useNavigate();

  const { id } = useParams();

  const isSelectDisabled = useMemo(() => {
    if (
      datasetSelectMode === "optimizeDataset" &&
      selectedDataset.length === 1
    ) {
      return true;
    }

    return false;
  }, [datasetSelectMode, selectedDataset]);

  return (
    <Box sx={{ height: "calc(100vh - 190px)", width: "100%" }}>
      <TableContainer
        style={{ width: "100%", height: "100%", overflow: "auto" }}
        ref={scrollContainerRef}
      >
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {datasetSelectMode ? (
                <CustomTableCell sx={{ width: "20px" }}>
                  <CustomTooltip
                    show={datasetSelectMode === "optimizeDataset"}
                    placement="right"
                    arrow
                    title="You can choose only 1 dataset at a time for optimization"
                  >
                    <SecondaryCheckbox
                      checked={
                        allSelectedDataset ||
                        selectedDataset?.length === totalCount
                          ? totalCount !== 0
                          : null
                      }
                      onChange={(e, checked) => {
                        e.stopPropagation();
                        if (datasetSelectMode === "optimizeDataset") {
                          return;
                        }
                        setSelectedDataset([]);
                        setAllSelectedDataset(checked);
                      }}
                      sx={{ padding: 0 }}
                    />
                  </CustomTooltip>
                </CustomTableCell>
              ) : null}
              {enabledColumns?.map(({ label, value }) => (
                <CustomTableCell key={value}>{label}</CustomTableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {datasetData?.map((row) => {
              const dataset = `${row?.environment}-${row?.version}`;
              const isSelected = Boolean(
                allSelectedDataset ||
                  selectedDataset.find((d) => d === dataset),
              );

              return (
                <TableRow
                  key={dataset}
                  sx={{
                    "&:hover": {
                      cursor: "pointer",
                      backgroundColor: "action.hover",
                    },
                  }}
                >
                  {datasetSelectMode ? (
                    <CustomTableCell>
                      <CustomTooltip
                        show={isSelectDisabled ? !isSelected : null}
                        placement="right"
                        arrow
                        title="You can choose only 1 dataset at a time for optimization"
                      >
                        <SecondaryCheckbox
                          checked={isSelected}
                          sx={{ padding: 0 }}
                          onChange={(e, checked) => {
                            e.stopPropagation();
                            if (isSelectDisabled && !isSelected) {
                              return;
                            }
                            if (checked) {
                              setSelectedDataset((p) => [...p, dataset]);
                            } else {
                              if (allSelectedDataset) {
                                setAllSelectedDataset(false);
                                setSelectedDataset(
                                  datasetData?.reduce((acc, curr) => {
                                    const eachDataset = `${curr?.environment}-${curr?.version}`;
                                    if (eachDataset !== dataset) {
                                      acc.push(eachDataset);
                                    }
                                    return acc;
                                  }, []),
                                );
                              } else {
                                setSelectedDataset((prevState) =>
                                  prevState.filter((d) => d !== dataset),
                                );
                              }
                            }
                          }}
                        />
                      </CustomTooltip>
                    </CustomTableCell>
                  ) : null}
                  {enabledColumns?.map(({ value }) => {
                    const val = ["startDate", "endDate"].includes(value)
                      ? format(new Date(row?.[value]), "yyyy-MM-dd")
                      : row?.[value];
                    return (
                      <CustomTableCell
                        onClick={() =>
                          navigate(
                            `/dashboard/models/${id}/datasets/${dataset}`,
                          )
                        }
                        key={value}
                      >
                        {val}
                      </CustomTableCell>
                    );
                  })}
                </TableRow>
              );
            })}
            {isFetchingNextPage ? (
              <TableRow>
                <CustomTableCell colSpan={6} sx={{ textAlign: "center" }}>
                  <CircularProgress size={20} />
                </CustomTableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

DatasetTable.propTypes = {
  datasetData: PropTypes.array,
  fetchNextPage: PropTypes.func,
  isLoading: PropTypes.bool,
  isFetchingNextPage: PropTypes.bool,
  columns: PropTypes.array,
  datasetSelectMode: PropTypes.bool,
  selectedDataset: PropTypes.array,
  setSelectedDataset: PropTypes.func,
  allSelectedDataset: PropTypes.bool,
  setAllSelectedDataset: PropTypes.func,
  totalCount: PropTypes.number,
};

export default DatasetTable;
