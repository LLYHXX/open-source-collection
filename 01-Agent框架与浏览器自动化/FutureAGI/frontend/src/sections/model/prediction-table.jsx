import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import PropTypes from "prop-types";
import Scrollbar from "src/components/scrollbar";

export default function PredictionTable({ tableData, properties }) {
  const propsToShow = properties
    ? properties?.filter((value) => value.selected)
    : [];

  return (
    <>
      <TableContainer sx={{ position: "relative", overflow: "unset" }}>
        <Scrollbar>
          <Table sx={{ minWidth: 800 }} stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell />
                {propsToShow.map((value, index) => {
                  return <TableCell key={index}>{value.name}</TableCell>;
                })}
              </TableRow>
            </TableHead>

            <TableBody key="main-table">
              {tableData?.map((row, index) => (
                <PredictionTableRow
                  idNum={index + 1}
                  key={index}
                  row={row}
                  propsToShow={propsToShow}
                />
              ))}
            </TableBody>
          </Table>
        </Scrollbar>
      </TableContainer>
    </>
  );
}

PredictionTable.propTypes = {
  tableData: PropTypes.array,
  properties: PropTypes.array,
};

// ----------------------------------------------------------------------

function PredictionTableRow({ row, propsToShow }) {
  return (
    <>
      <TableRow>
        {propsToShow.map((value, index) => {
          return (
            <TableCell key={index}>
              {row[value.name] || row.properties[value.name]}
            </TableCell>
          );
        })}
      </TableRow>
    </>
  );
}

PredictionTableRow.propTypes = {
  row: PropTypes.object,
  propsToShow: PropTypes.array,
  idNum: PropTypes.number,
};
