import { trackEvent, Events } from "../Mixpanel";

import { menuIcons } from "./svgIcons";

export const setMenuIcons = (params, datasetName) => {
  return params.defaultItems.map((item) => {
    switch (item) {
      case "resetColumns":
        return {
          name: "Reset Columns",
          action: () => {
            params.api.resetColumnState();
            params.api.sizeColumnsToFit();
            trackEvent(Events.columnResetClicked);
          },
          icon: menuIcons[item], // Replace with your desired icon
        };
      case "autoSizeThis":
        return {
          name: "Autosize This Column",
          action: () => {
            const column = params.column;
            params.api.autoSizeColumns([column.getColId()]);
            trackEvent(Events.columnAutosizeClicked);
          },
          icon: menuIcons[item],
        };
      case "autoSizeAll":
        return {
          name: "Autosize All Columns",
          action: () => {
            const allColumnIds = params?.api
              ?.getColumns()
              ?.map((col) => col?.getId());
            params.api.autoSizeColumns(allColumnIds);
            trackEvent(Events.allColumnsAutosizeClicked);
          },
          icon: menuIcons[item],
        };
      case "sortAscending":
        return {
          name: "Sort Ascending",
          action: () => {
            const columnName = params?.column?.getColId();
            const columnDef = params?.column?.getColDef();
            const columnNameToLog = columnDef.headerName || columnDef.field;

            params.api.applyColumnState({
              state: [{ colId: columnName, sort: "asc" }],
              defaultState: { sort: null },
            });
            trackEvent(Events.columnSortingClicked, {
              dataset_name: datasetName,
              sortedColumnName: columnNameToLog,
              sortOrder: "asc",
            });
          },
          icon: menuIcons[item],
        };
      case "sortUnSort":
        return {
          name: "Clear Sort",
          action: () => {
            return params.api.applyColumnState({
              state: [{ colId: params?.column?.getColId(), sort: null }],
              defaultState: { sort: null },
            });
          },
          icon: menuIcons[item],
        };
      case "sortDescending":
        return {
          name: "Sort Descending",
          action: () => {
            const columnName = params.column.getColId();
            const columnDef = params.column.getColDef();
            const columnNameToLog = columnDef.headerName || columnDef.field;
            params.api.applyColumnState({
              state: [{ colId: columnName, sort: "desc" }],
              defaultState: { sort: null },
            });
            trackEvent(Events.columnSortingClicked, {
              dataset_name: datasetName,
              sortedColumnName: columnNameToLog,
              sortOrder: "desc",
            });
          },
          icon: menuIcons[item], // Replace with your desired icon
        };
      case "pinSubMenu": {
        const columnPinned = params.column.getPinned();
        return {
          name: "Pin Column",
          subMenu: [
            {
              name: "No Pin",
              action: () => params.api.setColumnsPinned([params.column], null),
              icon: !columnPinned ? menuIcons.correct : null,
            },
            {
              name: "Pin Left",
              action: () =>
                params.api.setColumnsPinned([params.column], "left"),
              icon: columnPinned === "left" ? menuIcons.correct : null,
            },
            {
              name: "Pin Right",
              action: () =>
                params.api.setColumnsPinned([params.column], "right"),
              icon: columnPinned === "right" ? menuIcons.correct : null,
            },
          ],
          icon: menuIcons[item],
        };
      }
      case "columnChooser":
        return {
          name: "Choose Columns",
          action: () => {
            params.api.showColumnChooser();
            // trackEvent(Events.columnChooseClicked);
          },
          icon: menuIcons[item],
        };
      default:
        return item;
    }
  });
};

export const reorderMenuList = (mainMenuItems, menuOrder, separatorList) => {
  const rearrangedItems = menuOrder.flatMap((name) => {
    const item = mainMenuItems.find(
      (item) => (typeof item === "string" ? item : item.name) === name,
    );
    if (typeof item !== "string" && separatorList?.includes(item?.name)) {
      return [item, "separator"];
    }
    return item;
  });
  return rearrangedItems.filter((item) => item !== undefined && item !== null);
};
