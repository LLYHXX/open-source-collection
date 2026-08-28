import React, { useState } from "react";
import { SingleImageViewContext } from "./SingleImageContext";
import PropTypes from "prop-types";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";

const SingleImageViewerProvider = ({ children }) => {
  const [imageUrl, setImageUrl] = useState(null);

  return (
    <SingleImageViewContext.Provider value={{ imageUrl, setImageUrl }}>
      {children}
      <Lightbox
        open={Boolean(imageUrl)}
        close={() => {
          setImageUrl(null);
        }}
        slides={[{ src: imageUrl }]}
        render={{
          buttonPrev: () => null,
          buttonNext: () => null,
        }}
        carousel={{
          finite: true,
        }}
      />
    </SingleImageViewContext.Provider>
  );
};

SingleImageViewerProvider.propTypes = {
  children: PropTypes.node,
};

export default SingleImageViewerProvider;
