import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Box,
  FormHelperText,
  MenuItem,
  Paper,
  Popper,
  useTheme,
} from "@mui/material";
import { useController } from "react-hook-form";
import PropTypes from "prop-types";

const startRegex = /.*{{[^}\s]*(?!}})$/;

const ConditionalInput = ({ control, fieldName, allColumns }) => {
  const theme = useTheme();
  const [showDropdown, setShowDropdown] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState({ x: 0, y: 0 });
  const [selectedIndex, setSelectedIndex] = useState(0);
  const textareaRef = useRef(null);
  const popperRef = useRef(null);

  const { field, fieldState } = useController({
    control,
    name: fieldName,
  });

  const errorMessage = fieldState.error?.message;
  const isError = !!errorMessage;

  const searchText = useMemo(() => {
    const textarea = textareaRef.current;
    if (!textarea) return "";
    const { selectionStart } = textarea;
    const textBeforeCursor = field.value.substring(0, selectionStart);

    if (!startRegex.test(textBeforeCursor)) return "";
    const lastOpenBracketIndex = textBeforeCursor.lastIndexOf("{{");

    return textBeforeCursor.substring(lastOpenBracketIndex + 2, selectionStart);
  }, [field.value]);

  const columnOptions = useMemo(() => {
    return allColumns.reduce((filtered, column) => {
      if (
        column?.headerName?.toLowerCase().startsWith(searchText.toLowerCase())
      ) {
        filtered.push({
          label: column.headerName,
          value: `{{${column.headerName}}}`,
        });
      }
      return filtered;
    }, []);
  }, [allColumns, searchText]);

  const onCloseDropdown = () => {
    setShowDropdown(false);
    setSelectedIndex(0);
  };

  const getCaretCoordinates = (element, position) => {
    const { offsetLeft, offsetTop } = element;
    const div = document.createElement("div");
    const style = getComputedStyle(element);

    div.style.fontSize = style.fontSize;
    div.style.fontFamily = style.fontFamily;
    div.style.padding = style.padding;
    div.style.position = "absolute";
    div.style.whiteSpace = "pre-wrap";
    div.textContent = element.value.substring(0, position);

    const span = document.createElement("span");
    span.textContent = element.value.substring(position) || ".";
    div.appendChild(span);

    document.body.appendChild(div);
    const coordinates = {
      left: offsetLeft + span.offsetLeft,
      top: offsetTop + span.offsetTop,
      height: span.offsetHeight,
    };
    document.body.removeChild(div);

    return coordinates;
  };

  const setDropDownPos = () => {
    const textarea = textareaRef.current;
    const { selectionStart } = textarea;
    const cursorCoords = getCaretCoordinates(textarea, selectionStart);
    const rect = textarea.getBoundingClientRect();

    setDropdownPosition({
      x: rect.left + cursorCoords.left,
      y: rect.top + cursorCoords.top + cursorCoords.height,
    });
  };

  useEffect(() => {
    window.addEventListener("resize", setDropDownPos);
    return () => window.removeEventListener("resize", setDropDownPos);
  }, []);

  const handleChange = (content) => {
    field.onChange(content);
    const textarea = textareaRef.current;
    const { selectionStart } = textarea;
    const textBeforeCursor = content.substring(0, selectionStart);

    if (startRegex.test(textBeforeCursor)) {
      setDropDownPos();
      setShowDropdown(true);
    } else {
      onCloseDropdown();
    }
  };

  const handleVariableSelect = (variable) => {
    const textarea = textareaRef.current;
    const { selectionStart } = textarea;
    const content = textarea.value;
    const textBeforeCursor = content.substring(0, selectionStart);
    const lastOpenBracketIndex = textBeforeCursor.lastIndexOf("{{");

    const newContent =
      content.substring(0, lastOpenBracketIndex) +
      variable.value +
      content.substring(selectionStart);

    field.onChange(newContent);
    onCloseDropdown();

    setTimeout(() => {
      const newCursorPosition = lastOpenBracketIndex + variable.value.length;
      textarea.selectionEnd = newCursorPosition;
      textarea.selectionStart = newCursorPosition;
    }, 0);
  };

  const onKeyDown = (e) => {
    e.stopPropagation();

    if (e.key === "Escape") {
      onCloseDropdown();
    } else if (e.key === "ArrowDown" && showDropdown) {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % columnOptions.length);
    } else if (e.key === "ArrowUp" && showDropdown) {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev > 0 ? prev - 1 : columnOptions.length - 1,
      );
    } else if (e.key === "Enter" && showDropdown) {
      e.preventDefault();
      handleVariableSelect(columnOptions[selectedIndex]);
    }
  };

  return (
    <Box sx={{ position: "relative", width: "100%" }}>
      <textarea
        ref={textareaRef}
        value={field.value}
        onChange={(e) => handleChange(e.target.value)}
        onBlur={field.onBlur}
        onKeyDown={onKeyDown}
        placeholder="Type condition here... Use {{ to access variables"
        style={{
          width: "100%",
          minHeight: "90px",
          padding: "8px",
          border: `1px solid ${theme.palette.divider}`,
          resize: "none",
          fontFamily: "inherit",
          outline: "none",
          backgroundColor: theme.palette.background.default,
          borderRadius: "8px",
          color: theme.palette.text.primary,
        }}
      />

      <Popper
        ref={popperRef}
        open={showDropdown}
        style={{
          position: "absolute",
          transform: `translate(${dropdownPosition.x}px, ${dropdownPosition.y}px)`,
          zIndex: 9999,
        }}
        placement="bottom-start"
        disablePortal={false}
        role="listbox"
      >
        <Paper elevation={3} sx={{ p: 0.5, maxHeight: 150, overflow: "auto" }}>
          {columnOptions.map((variable, index) => (
            <MenuItem
              key={variable.value}
              onClick={() => handleVariableSelect(variable)}
              selected={index === selectedIndex}
              sx={{
                minWidth: 150,
                backgroundColor:
                  index === selectedIndex ? "background.neutral" : "inherit",
                "&:hover": { backgroundColor: "action.hover" },
                "&:focus": { outline: "none" },
              }}
            >
              {variable.label}
            </MenuItem>
          ))}
        </Paper>
      </Popper>

      {/* <Typography color="text.secondary" variant="subtitle2" fontWeight={400} sx={{ mt: 1 }}>
        use
        <Typography component="span" color="primary">
          {" {{ "}
        </Typography>
        to access variables
      </Typography> */}

      {isError && (
        <FormHelperText sx={{ paddingLeft: 1, marginTop: 0 }} error>
          {errorMessage}
        </FormHelperText>
      )}
    </Box>
  );
};

ConditionalInput.propTypes = {
  control: PropTypes.object.isRequired,
  fieldName: PropTypes.string.isRequired,
  allColumns: PropTypes.array.isRequired,
};

export default ConditionalInput;
