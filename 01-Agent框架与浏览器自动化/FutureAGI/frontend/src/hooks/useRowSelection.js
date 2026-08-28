import { useState } from "react";

export const useRowSelection = () => {
  const [rowSelected, setRowSelected] = useState([]);

  return {
    rowSelected,
    setRowSelected,
  };
};
