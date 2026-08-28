import { format } from "date-fns";
import _ from "lodash";

function isNumeric(value) {
  return _.isFinite(_.toNumber(value));
}

function isValidDate(value) {
  const date = new Date(value);
  return !isNaN(date.getTime());
}

export const validateDatasetFilter = (acc, currVal) => {
  if (
    currVal.dataType === "string" &&
    currVal?.operator?.length &&
    currVal?.value?.[0] !== undefined
  ) {
    const { id, ...rest } = currVal;
    acc.push({ ...rest });
    return acc;
  }

  if (currVal.dataType === "number" && currVal?.operator?.length) {
    const { id, ...rest } = currVal;
    const operator = currVal?.operator;
    if (
      ["between", "notBetween"].includes(operator) &&
      Array.isArray(currVal?.value) &&
      currVal?.value?.[0]?.length &&
      currVal?.value?.[1]?.length &&
      isNumeric(currVal?.value?.[0]) &&
      isNumeric(currVal?.value?.[1])
    ) {
      acc.push({
        ...rest,
        value: rest?.value?.map((v) => parseFloat(v)),
      });
      return acc;
    }

    if (
      !["between", "notBetween"].includes(operator) &&
      Array.isArray(currVal?.value) &&
      currVal?.value?.[0]?.length &&
      isNumeric(currVal?.value?.[0])
    ) {
      acc.push({ ...rest, value: [parseFloat(rest?.value?.[0])] });
      return acc;
    }
  }

  if (currVal.dataType === "date" && currVal?.operator?.length) {
    const { id, ...rest } = currVal;
    const operator = currVal?.operator;
    if (
      ["between", "notBetween"].includes(operator) &&
      Array.isArray(currVal?.value) &&
      currVal?.value?.[0] &&
      currVal?.value?.[1] &&
      isValidDate(currVal?.value?.[0]) &&
      isValidDate(currVal?.value?.[1])
    ) {
      acc.push({
        ...rest,
        value: rest?.value?.map((d) => format(d, "yyyy-MM-dd")),
      });
      return acc;
    }

    if (
      !["between", "notBetween"].includes(operator) &&
      Array.isArray(currVal?.value) &&
      currVal?.value?.[0] &&
      isValidDate(currVal?.value?.[0])
    ) {
      acc.push({ ...rest, value: [format(rest?.value?.[0], "yyyy-MM-dd")] });
      return acc;
    }
  }

  return acc;
};
