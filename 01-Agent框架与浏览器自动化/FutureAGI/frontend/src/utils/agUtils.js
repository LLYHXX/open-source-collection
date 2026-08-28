import { AGGridCellDataType } from "./constant";

export const parseCellValue = (cellValue, cellDataType) => {
  if (cellDataType === AGGridCellDataType.integer) {
    return parseInt(cellValue);
  }
  return cellValue;
};
