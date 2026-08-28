import PropTypes from "prop-types";
import Table from "@mui/material/Table";
import Paper from "@mui/material/Paper";
import TableRow from "@mui/material/TableRow";
import Collapse from "@mui/material/Collapse";
import TableHead from "@mui/material/TableHead";
import TableCell from "@mui/material/TableCell";
import TableBody from "@mui/material/TableBody";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import TableContainer from "@mui/material/TableContainer";
import { useBoolean } from "src/hooks/use-boolean";
import Iconify from "src/components/iconify";
import Scrollbar from "src/components/scrollbar";
import React from "react";
// import { LabelNer } from "src/components/annotate";
import { JsonCodeView } from "src/components/code";

export default function EventsCollapsibleTable({ tableData, properties }) {
  const propsToShow = properties?.filter((value) => value.selected);

  return (
    <TableContainer>
      <Scrollbar>
        <Table sx={{ minWidth: 800 }} size="small" stickyHeader>
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
              <CollapsibleTableRow
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
  );
}

EventsCollapsibleTable.propTypes = {
  tableData: PropTypes.array,
  properties: PropTypes.array,
  handleScrollBottom: PropTypes.func,
  hasMoreData: PropTypes.bool,
  loading: PropTypes.bool,
};

// ----------------------------------------------------------------------

function CollapsibleTableRow({ row, propsToShow }) {
  const collapsible = useBoolean();

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

        {propsToShow.map((value, index) => {
          return (
            <TableCell key={index}>
              {row[value.name] || row.properties[value.name]}
            </TableCell>
          );
        })}
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
              {/* TODO: button to add to annotation task */}

              <Typography variant="h6" sx={{ m: 2, mt: 0 }}>
                Model Predictions
              </Typography>
              {/* 
              <LabelNer
                idNum={idNum}
                nerData={nerData}
                entityTypes={labels}
                isEditable={false}
              ></LabelNer> */}

              <Typography variant="h6" sx={{ m: 2, mt: 0 }}>
                All Data
              </Typography>

              <JsonCodeView data={row} />
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
