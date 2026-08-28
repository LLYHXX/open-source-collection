import { format } from "date-fns";

export const getDateOptionTitle = (option, isSelected, dateFilter) => {
  if (option === "Custom" && isSelected) {
    return `${format(new Date(dateFilter[0]), "dd/MM/yyyy")} - ${format(new Date(dateFilter[1]), "dd/MM/yyyy")}`;
  }

  return option;
};

export const formatDate = (date) => format(date, "yyyy-MM-dd HH:mm:ss");

export const getUniqueId = () => {
  const timestamp = Date.now().toString(36); // Convert the current timestamp to a base-36 string
  const randomNum = Math.random().toString(36).substring(2, 10); // Generate a random base-36 string
  return timestamp + randomNum;
};

export const createUniqueObject = (value, key = "value") => {
  let obj = {
    id: getUniqueId(),
  };
  if (typeof value === "object") {
    obj = { ...obj, ...value };
  } else {
    obj[key] = value;
  }

  return obj;
};

export const formatDateBasedOnAggregation = (d, selectedAggregation) => {
  if (selectedAggregation === "daily") {
    return format(d, "dd MMM");
  } else if (selectedAggregation === "hourly") {
    return format(d, "dd MMM, h aaa");
  } else if (selectedAggregation === "weekly") {
    return format(d, "dd MMM");
  } else if (selectedAggregation === "monthly") {
    return format(d, "MMM");
  }
};

export const traverseObject = (obj, caller, path = []) => {
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === "object" && !Array.isArray(value) && value !== null) {
      traverseObject(value, caller, [...path, key]);
    } else {
      caller([...path, key], value);
    }
  }
};

export const validateBreakdown = (eachBreakdown) => {
  return Boolean(eachBreakdown?.value?.length);
};

export const validateFilter = (eachFilter) => {
  return (
    Boolean(eachFilter?.key?.length) &&
    Boolean(eachFilter?.value?.filter((v) => v.length)?.length)
  );
};

export const validateMetric = (acc, curr) => {
  if (curr?.databaseId?.length) {
    acc.push({
      ...curr,
      filters: curr?.filters?.filter(validateFilter),
    });
  }
  return acc;
};

export const removeId = (v) => {
  const { id, ...rest } = v;

  return { ...rest };
};

export const formatBreakdown = (v) => {
  return v?.value;
};
