import React, { useState, useEffect, useRef } from "react";
import Markdown from "react-markdown";
import "./StreamingText.css";
import PropTypes from "prop-types";

const StreamingText = ({
  text = "",
  speed = 10,
  className = "",
  isAnimating = true, // Control animation with this prop
  onAnimationComplete = () => {}, // Callback when animation completes
}) => {
  const [visibleLength, setVisibleLength] = useState(0);
  const intervalRef = useRef(null);
  const textLengthRef = useRef(0);

  // Reset and start animation when text changes
  useEffect(() => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    if (!isAnimating) {
      setVisibleLength(text.length);
      onAnimationComplete();
      return;
    }

    // If new text is shorter than what's currently displayed,
    // reset the visible length
    if (text.length < visibleLength) {
      setVisibleLength(0);
      textLengthRef.current = text.length;
    } else {
      textLengthRef.current = text.length;
    }

    // Start the animation interval
    intervalRef.current = setInterval(() => {
      setVisibleLength((prev) => {
        if (prev < textLengthRef.current) {
          return prev + 1;
        } else {
          onAnimationComplete();
          clearInterval(intervalRef.current);
          return prev;
        }
      });
    }, speed);

    // Clean up interval on unmount or text change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [text, speed]);

  // The visible portion of the text
  const visibleText = text.slice(0, visibleLength);

  return (
    <div className={`streaming-text ${className}`}>
      <div className="fade-in-text">
        <Markdown>{visibleText}</Markdown>
      </div>
    </div>
  );
};

StreamingText.propTypes = {
  text: PropTypes.string,
  speed: PropTypes.number,
  className: PropTypes.string,
  isAnimating: PropTypes.bool,
  onAnimationComplete: PropTypes.func,
};

export default StreamingText;
