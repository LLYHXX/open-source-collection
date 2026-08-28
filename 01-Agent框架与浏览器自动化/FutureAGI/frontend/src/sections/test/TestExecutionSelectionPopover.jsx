import {
  Box,
  Checkbox,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Popover,
  Skeleton,
  Typography,
  useTheme,
} from "@mui/material";
import React, { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { useInfiniteQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { useParams } from "react-router";
import { useScrollEnd } from "src/hooks/use-scroll-end";
import { ShowComponent } from "src/components/show";
import FormSearchField from "src/components/FormSearchField/FormSearchField";
import { useSelectedExecutionsStore } from "./states";

const TestExecutionSelectionSkeletonItem = () => (
  <Box sx={{ display: "flex", gap: 1, padding: 1, alignItems: "center" }}>
    <Skeleton variant="rounded" width={20} height={15} />
    <Skeleton variant="rounded" width="100%" height={15} />
  </Box>
);

const TestExecutionSelectionChild = () => {
  const { testId } = useParams();
  const [search, setSearch] = useState("");
  const theme = useTheme();

  const { selectedExecutions, setSelectedExecutions } =
    useSelectedExecutionsStore();

  const { data, isFetchingNextPage, fetchNextPage, isPending } =
    useInfiniteQuery({
      queryFn: async ({ pageParam = 1 }) => {
        const response = await axios.get(
          endpoints.runTests.detailExecutions(testId),
          {
            params: {
              page: pageParam,
              search: search,
            },
          },
        );
        return response.data;
      },
      queryKey: ["test-runs-executions", testId, search],
      staleTime: Infinity,
      getNextPageParam: ({ next, current_page }) =>
        next ? current_page + 1 : null,
      initialPageParam: 1,
    });

  const testExecutionsList = useMemo(
    () => data?.pages.flatMap((page) => page.results),
    [data],
  );

  useEffect(() => {
    if (selectedExecutions.length === 0 && testExecutionsList?.length > 0) {
      setSelectedExecutions(testExecutionsList?.slice(0, 5));
    }
  }, [testExecutionsList, setSelectedExecutions, selectedExecutions]);

  const scrollContainer = useScrollEnd(() => {
    if (isPending || isFetchingNextPage) return;
    fetchNextPage();
  }, [fetchNextPage, isFetchingNextPage, isPending]);

  return (
    <Box>
      <Box>
        <FormSearchField
          placeholder="Search Executions..."
          size="small"
          searchQuery={search}
          onChange={(e) => setSearch(e.target.value)}
          fullWidth
          autoFocus
          sx={{
            margin: theme.spacing(1),
            width: `calc(100% - ${theme.spacing(2)})`,
          }}
          InputProps={{}}
        />
      </Box>
      <ShowComponent condition={testExecutionsList?.length === 0}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            flexDirection: "column",
            height: "100%",
            padding: 4,
          }}
        >
          <Typography typography="s1" fontWeight="fontWeightMedium">
            No test executions found
          </Typography>
          <Typography typography="s3">
            You need to run a test to see the executions
          </Typography>
        </Box>
      </ShowComponent>
      <List
        sx={{
          width: "100%",
          maxWidth: 400,
          bgcolor: "background.paper",
          maxHeight: 200,
          paddingX: 0.5,
          overflowY: "auto",
        }}
        ref={scrollContainer}
        dense
      >
        <ShowComponent condition={isPending}>
          <TestExecutionSelectionSkeletonItem />
          <TestExecutionSelectionSkeletonItem />
        </ShowComponent>
        <ShowComponent condition={!isPending}>
          {testExecutionsList?.map((execution) => {
            const { id, scenarios } = execution;
            const labelId = `checkbox-list-label-${id}`;
            const isSelected = selectedExecutions?.some(
              ({ id: selectedId }) => selectedId === id,
            );

            return (
              <ListItem key={id} disablePadding>
                <ListItemButton
                  role={undefined}
                  onClick={() => {
                    const isSelected = selectedExecutions.find(
                      (item) => item.id === id,
                    );
                    if (isSelected) {
                      setSelectedExecutions((prev) =>
                        prev.filter((item) => item.id !== id),
                      );
                    } else {
                      setSelectedExecutions((prev) => [...prev, execution]);
                    }
                  }}
                  dense
                >
                  <ListItemIcon>
                    <Checkbox
                      edge="start"
                      checked={isSelected}
                      tabIndex={-1}
                      disableRipple
                      inputProps={{ "aria-labelledby": labelId }}
                      sx={{ padding: 0 }}
                    />
                  </ListItemIcon>
                  <ListItemText
                    id={labelId}
                    primary={`Execution ${id.slice(0, 8)}`}
                    secondary={`Scenario : ${scenarios}`}
                    primaryTypographyProps={{
                      typography: "s2",
                      fontWeight: "medium",
                    }}
                    secondaryTypographyProps={{ typography: "s2" }}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </ShowComponent>
        <ShowComponent condition={isFetchingNextPage}>
          <TestExecutionSelectionSkeletonItem />
          <TestExecutionSelectionSkeletonItem />
          <TestExecutionSelectionSkeletonItem />
        </ShowComponent>
      </List>
    </Box>
  );
};

const TestExecutionSelectionPopover = ({ open, onClose, anchor }) => {
  return (
    <Popover
      open={open}
      onClose={onClose}
      anchorEl={anchor}
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
      transformOrigin={{
        vertical: "top",
        horizontal: "right",
      }}
      PaperProps={{
        sx: {
          minWidth: anchor?.clientWidth,
        },
      }}
    >
      <TestExecutionSelectionChild />
    </Popover>
  );
};

TestExecutionSelectionPopover.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  anchor: PropTypes.object,
};

export default TestExecutionSelectionPopover;
