//@ts-nocheck
import React, { useMemo, useState } from "react";
import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import _ from "lodash";
import { useInfiniteQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import CreateSecretModal from "./CreateSecretModal";
import { FormSearchSelectFieldControl } from "src/components/FromSearchSelectField";

const SecretSelect = ({
  control,
  fieldName,
  fullWidth,
  dropDownMaxHeight,
  helperText,
  ...rest
}) => {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const {
    data: secretList,
    isLoading,
    isFetchingNextPage,
    fetchNextPage,
  } = useInfiniteQuery({
    queryKey: ["secrets"],
    queryFn: ({ pageParam }) =>
      axios.get(endpoints.secrets.list, { params: { page: pageParam } }),
    getNextPageParam: (o) => (o.data.next ? o.data.current_page + 1 : null),
    initialPageParam: 1,
  });

  const options = useMemo(
    () =>
      secretList?.pages.reduce(
        (acc, curr) => [...acc, ...curr.data.results],
        [],
      ) || [],
    [secretList],
  );

  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    if (scrollTop + clientHeight >= scrollHeight - 5) {
      if (!isFetchingNextPage || !isLoading) {
        fetchNextPage();
      }
    }
  };

  return (
    <>
      <CreateSecretModal
        open={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
      />
      <FormSearchSelectFieldControl
        label={rest.label}
        fullWidth={fullWidth}
        size={rest?.size}
        control={control}
        isFetchingNextPage={isFetchingNextPage}
        onScrollEnd={handleScroll}
        fieldName={fieldName}
        createLabel="Create Secret"
        handleCreateLabel={() => setIsCreateOpen(true)}
        options={options.map((option) => ({
          value: option.id,
          label: option.name,
          component: (
            <Box>
              <Typography
                variant="caption"
                fontWeight={500}
                component="div"
                sx={{
                  textOverflow: "ellipsis",
                  overflowX: "hidden",
                  textWrap: "nowrap",
                }}
              >
                {option.name}
              </Typography>
              <Typography variant="caption">{option.maskedKey}</Typography>
            </Box>
          ),
        }))}
      />
    </>
  );
};

SecretSelect.propTypes = {
  control: PropTypes.object,
  fieldName: PropTypes.string,
  size: PropTypes.string,
  label: PropTypes.string,
  fullWidth: PropTypes.bool,
  dropDownMaxHeight: PropTypes.number,
  helperText: PropTypes.string,
};

export default SecretSelect;
