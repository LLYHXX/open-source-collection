import { createContext, useContext } from "react";

export const MultiImageViewContext = createContext({
  images: [],
  startIndex: 0,
  setImages: () => {},
});

export const useMultiImageViewContext = () => {
  return useContext(MultiImageViewContext);
};
