import React from "react";
import {
  Container,
  ListItemText,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import Scrollbar from "src/components/scrollbar";
import { useSettingsContext } from "src/components/settings";

export default function DriftBreakdownTable() {
  const settings = useSettingsContext();
  return (
    <>
      <Container maxWidth={settings.themeStretch ? false : "xl"}>
        <TableContainer>
          <Scrollbar>
            <Table sx={{ minWidth: 800 }} stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell />
                </TableRow>
              </TableHead>

              <TableBody key="main-table">
                <TableRow>
                  <TableCell>
                    <ListItemText
                      primary={"feature"}
                      secondary={"type"}
                      primaryTypographyProps={{ typography: "body2" }}
                      secondaryTypographyProps={{
                        component: "span",
                        color: "text.disabled",
                      }}
                    />
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Scrollbar>
        </TableContainer>
      </Container>
    </>
  );
}

DriftBreakdownTable.propTypes = {};
