import { createContext, useContext } from "react";

export const SingleImageViewContext = createContext({
  imageUrl: null,
  setImageUrl: () => {},
});

export const useSingleImageViewContext = () => {
  return useContext(SingleImageViewContext);
};
