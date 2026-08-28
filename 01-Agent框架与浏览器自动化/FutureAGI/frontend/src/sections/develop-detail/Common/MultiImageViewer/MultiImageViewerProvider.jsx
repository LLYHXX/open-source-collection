import React, { useState, useCallback } from "react";
import { MultiImageViewContext } from "./MultiImageContext";
import PropTypes from "prop-types";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";

const MultiImageViewerProvider = ({ children }) => {
  const [images, setImagesState] = useState([]);
  const [startIndex, setStartIndex] = useState(0);

  const setImages = useCallback((imageUrls, index = 0) => {
    if (!imageUrls || imageUrls.length === 0) {
      setImagesState([]);
      setStartIndex(0);
    } else {
      setImagesState(imageUrls);
      setStartIndex(index);
    }
  }, []);

  const slides = images.map((url) => ({ src: url }));
  const isMultiple = images.length > 1;

  return (
    <MultiImageViewContext.Provider value={{ images, startIndex, setImages }}>
      {children}
      <Lightbox
        open={images.length > 0}
        close={() => setImages([])}
        slides={slides}
        index={startIndex}
        render={{
          buttonPrev: isMultiple ? undefined : () => null,
          buttonNext: isMultiple ? undefined : () => null,
        }}
        carousel={{
          finite: true,
        }}
      />
    </MultiImageViewContext.Provider>
  );
};

MultiImageViewerProvider.propTypes = {
  children: PropTypes.node,
};

export default MultiImageViewerProvider;
