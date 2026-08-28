// //@ts-nocheck
// import React, { useEffect, useMemo, useRef, useState } from "react";
// import { Controller } from "react-hook-form";
// import {
//   Box,
//   FormControl,
//   FormHelperText,
//   InputLabel,
//   MenuItem,
//   Popover,
//   Select,
//   Skeleton,
//   TextField,
// } from "@mui/material";
// import PropTypes from "prop-types";
// import _ from "lodash";
// import { useInfiniteQuery } from "@tanstack/react-query";
// import axios, { endpoints } from "src/utils/axios";
// import { useScrollEnd } from "src/hooks/use-scroll-end";
// import CustomModelSelectionPopover from "./CustomModelSelectionPopover";

// const CustomModelSelectionChild = ({
//   control,
//   fieldName,
//   valueSelector,
//   helperText,
//   fullWidth,
//   dropDownMaxHeight,
//   customMenuItem,
//   onConfigOpen,
//   ...rest
// }) => {
//   const [isOpen, setIsOpen] = useState(false);
//   const anchorEl = useRef(null);
//   const [search, setSearch] = useState("");

//   const {
//     data: modelList,
//     isLoading: isLoadingModelList,
//     fetchNextPage,
//     isFetchingNextPage,
//   } = useInfiniteQuery({
//     queryKey: ["model-list", search],
//     queryFn: ({ pageParam }) =>
//       axios.get(endpoints.develop.modelList, {
//         params: { page: pageParam, search: search },
//       }),
//     getNextPageParam: (o) => (o.data.next ? o.data.current_page + 1 : null),
//     initialPageParam: 1,
//   });

//   const options = useMemo(
//     () =>
//       modelList?.pages.reduce(
//         (acc, curr) => [...acc, ...curr.data.results],
//         [],
//       ) || [],
//     [modelList],
//   );

//   const scrollRef = useScrollEnd(() => {
//     if (isFetchingNextPage || isLoadingModelList) return;
//     fetchNextPage();
//   }, [isFetchingNextPage, isLoadingModelList]);

//   const handleOpen = () => {
//     setIsOpen(true);
//   };

//   const handleClose = () => {
//     setIsOpen(false);
//   };

//   return (
//     <Controller
//       render={({ field: { onChange, value }, formState: { errors } }) => {
//         const errorMessage = _.get(errors, `${fieldName}.message`);
//         const isError = !!errorMessage;
//         const selectedOption = options?.find((o) => o.model_name === value);

//         return (
//           <FormControl error={isError} fullWidth={fullWidth} size={rest?.size}>
//             <InputLabel>{rest.label}</InputLabel>
//             <Select
//               {...rest}
//               ref={anchorEl}
//               value={value || ""}
//               error={isError}
//               onOpen={handleOpen}
//               onClose={handleClose}
//               open={isOpen}
//               MenuProps={{
//                 PaperProps: {
//                   sx: {
//                     maxHeight: dropDownMaxHeight || 300,
//                   },
//                 },
//               }}
//             >
//               <MenuItem value={value}>
//                 {value}
//               </MenuItem>
//             </Select>

//             <CustomModelSelectionPopover
//               anchorEl={anchorEl}
//               options={options}
//               isLoadingModelList={isLoadingModelList}
//               isFetchingNextPage={isFetchingNextPage}
//               fetchNextPage={fetchNextPage}
//               onChange={onChange}
//               onConfigOpen={onConfigOpen}
//               setIsOpen={setIsOpen}
//               search={search}
//               setSearch={setSearch}
//               handleClose={handleClose}
//               isOpen={isOpen}
//             />
//             {(isError || helperText) && (
//               <FormHelperText>{errorMessage || helperText}</FormHelperText>
//             )}
//           </FormControl>
//         );
//       }}
//       control={control}
//       name={fieldName}
//     />
//   );
// };

// CustomModelSelectionChild.propTypes = {
//   control: PropTypes.any,
//   fieldName: PropTypes.string.isRequired,
//   valueSelector: PropTypes.func,
//   formControlProps: PropTypes.oneOfType([PropTypes.object, PropTypes.any]),
//   helperText: PropTypes.string,
//   fullWidth: PropTypes.bool,
//   dropDownMaxHeight: PropTypes.number,
//   onScrollEnd: PropTypes.func,
//   loadingMoreOptions: PropTypes.bool,
//   customMenuItem: PropTypes.func,
//   onConfigOpen: PropTypes.func,
// };

// // @ts-ignore
// export const CustomModelSelection = React.forwardRef(CustomModelSelectionChild);

//@ts-nocheck
import React, { useMemo, useRef, useState } from "react";
import { Controller } from "react-hook-form";
import { FormControl, FormHelperText } from "@mui/material";
import PropTypes from "prop-types";
import _ from "lodash";
import { useInfiniteQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { useScrollEnd } from "src/hooks/use-scroll-end";
import DropdownWithSearch from "src/sections/common/DropdownWithSearch";
import CustomModelSelectionPopover from "./CustomModelSelectionPopover";

const CustomModelSelectionChild = ({
  control,
  fieldName,
  valueSelector,
  helperText,
  fullWidth,
  dropDownMaxHeight,
  customMenuItem,
  onConfigOpen,
  valueIsObject,
  ...rest
}) => {
  const [search, setSearch] = useState("");
  const anchorRef = useRef(null);
  const [isOpen, setIsOpen] = useState(false);

  const {
    data: modelList,
    isLoading: isLoadingModelList,
    fetchNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["model-list", search],
    queryFn: ({ pageParam }) =>
      axios.get(endpoints.develop.modelList, {
        params: { page: pageParam, search: search },
      }),
    getNextPageParam: (o) => (o.data.next ? o.data.current_page + 1 : null),
    initialPageParam: 1,
  });

  const options = useMemo(
    () =>
      modelList?.pages.reduce(
        (acc, curr) => [...acc, ...curr.data.results],
        [],
      ) || [],
    [modelList],
  );

  const scrollRef = useScrollEnd(() => {
    if (isFetchingNextPage || isLoadingModelList) return;
    fetchNextPage();
  }, [isFetchingNextPage, isLoadingModelList]);

  const handleOpen = () => {
    setIsOpen(true);
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  return (
    <Controller
      render={({ field: { onChange, value }, formState: { errors } }) => {
        const errorMessage = _.get(errors, `${fieldName}.message`);
        const isError = !!errorMessage;

        return (
          <FormControl
            error={isError}
            fullWidth={fullWidth}
            size={rest?.size}
            sx={rest?.sx}
          >
            <DropdownWithSearch
              {...rest}
              label={rest.label}
              value={
                value?.model_name !== undefined
                  ? value?.model_name
                  : value || ""
              }
              options={[
                {
                  value: value || "",
                  label:
                    value?.model_name !== undefined
                      ? value?.model_name
                      : value || "",
                },
              ]}
              anchorRef={anchorRef}
              onOpen={handleOpen}
              onClose={handleClose}
              open={isOpen}
              error={isError}
              // onSelect={onChange}
              renderValue={(selected) => selected}
              popoverComponent={null}
              MenuProps={{
                PaperProps: {
                  sx: {
                    maxHeight: dropDownMaxHeight || 300,
                    display: "none",
                  },
                },
              }}
              iconUrl={value?.logoUrl}
            />

            <CustomModelSelectionPopover
              anchorEl={anchorRef}
              options={options}
              isLoadingModelList={isLoadingModelList}
              isFetchingNextPage={isFetchingNextPage}
              fetchNextPage={fetchNextPage}
              onChange={onChange}
              onConfigOpen={onConfigOpen}
              setIsOpen={setIsOpen}
              search={search}
              setSearch={setSearch}
              handleClose={handleClose}
              isOpen={isOpen}
              scrollRef={scrollRef}
              valueIsObject={valueIsObject}
            />

            {(isError || helperText) && (
              <FormHelperText>{errorMessage || helperText}</FormHelperText>
            )}
          </FormControl>
        );
      }}
      control={control}
      name={fieldName}
    />
  );
};

CustomModelSelectionChild.propTypes = {
  control: PropTypes.any,
  fieldName: PropTypes.string.isRequired,
  valueSelector: PropTypes.func,
  formControlProps: PropTypes.oneOfType([PropTypes.object, PropTypes.any]),
  helperText: PropTypes.string,
  fullWidth: PropTypes.bool,
  dropDownMaxHeight: PropTypes.number,
  onScrollEnd: PropTypes.func,
  loadingMoreOptions: PropTypes.bool,
  customMenuItem: PropTypes.func,
  onConfigOpen: PropTypes.func,
  setSelectedModelProvider: PropTypes.func,
  valueIsObject: PropTypes.bool,
};

// @ts-ignore
export const CustomModelSelection = React.forwardRef(CustomModelSelectionChild);
