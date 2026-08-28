import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Popover,
  Radio,
  useTheme,
  Skeleton,
  debounce,
} from "@mui/material";
import React, { useMemo, useState } from "react";
import PropTypes from "prop-types";
import { useInfiniteQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { useScrollEnd } from "../../../hooks/use-scroll-end";
import FormSearchField from "src/components/FormSearchField/FormSearchField";
import { useSelectedSimulatorAgentsStore } from "./states";
import { ShowComponent } from "../../../components/show";
import { useParams } from "react-router-dom";
import { useUpdateTestRuns } from "src/api/tests/testRuns";

const SimulatorSkeletonItem = () => (
  <Box sx={{ display: "flex", gap: 1, padding: 1, alignItems: "center" }}>
    <Skeleton variant="circular" width={20} height={15} />
    <Skeleton variant="rounded" width="100%" height={15} />
  </Box>
);

const SimulatorPopoverChild = () => {
  const [search, setSearch] = useState("");
  const theme = useTheme();
  const { testId } = useParams();

  const { mutate: updateTestRuns } = useUpdateTestRuns(testId);

  const debouncedUpdateTestRuns = React.useRef(
    debounce((data) => {
      updateTestRuns(data);
    }, 300),
  ).current;

  const { data, isFetchingNextPage, fetchNextPage, isPending } =
    useInfiniteQuery({
      queryFn: ({ pageParam }) =>
        axios.get(endpoints.simulatorAgents.list, {
          params: {
            page: pageParam,
            limit: 10,
            search,
          },
        }),
      queryKey: ["simulator-agent-list", search],
      getNextPageParam: ({ data }) =>
        data?.next ? data?.current_page + 1 : null,
      initialPageParam: 1,
    });

  const simulatorAgents = useMemo(
    () => data?.pages.flatMap((page) => page.data.results),
    [data],
  );

  const { selectedSimulatorAgent, setSelectedSimulatorAgent } =
    useSelectedSimulatorAgentsStore();

  const scrollContainer = useScrollEnd(() => {
    if (isPending || isFetchingNextPage) return;
    fetchNextPage();
  }, [fetchNextPage, isFetchingNextPage, isPending]);

  return (
    <Box>
      <Box>
        <FormSearchField
          placeholder="Search Simulators..."
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
      <List
        sx={{
          width: "100%",
          maxWidth: 400,
          bgcolor: "background.paper",
          maxHeight: 200,
          paddingX: 0.5,
          overflowY: "auto",
        }}
        dense
        ref={scrollContainer}
      >
        <ShowComponent condition={isPending}>
          <SimulatorSkeletonItem />
          <SimulatorSkeletonItem />
          <SimulatorSkeletonItem />
        </ShowComponent>
        <ShowComponent condition={!isPending}>
          {simulatorAgents?.map((agent) => {
            const { id, name } = agent;
            const labelId = `checkbox-list-label-${id}`;
            const isSelected = selectedSimulatorAgent?.id === id;

            return (
              <>
                <ListItem key={id} disablePadding>
                  <ListItemButton
                    role={undefined}
                    onClick={() => {
                      setSelectedSimulatorAgent(agent);
                      debouncedUpdateTestRuns({
                        simulator_agent_id: agent?.id,
                      });
                    }}
                    dense
                  >
                    <ListItemIcon>
                      <Radio
                        edge="start"
                        tabIndex={-1}
                        disableRipple
                        inputProps={{ "aria-labelledby": labelId }}
                        sx={{ padding: 0 }}
                        checked={isSelected}
                      />
                    </ListItemIcon>
                    <ListItemText
                      id={labelId}
                      primary={name}
                      primaryTypographyProps={{
                        typography: "s2",
                        fontWeight: "medium",
                      }}
                      secondaryTypographyProps={{ typography: "s2" }}
                    />
                  </ListItemButton>
                </ListItem>
              </>
            );
          })}
          <ShowComponent condition={isFetchingNextPage}>
            <>
              <SimulatorSkeletonItem />
              <SimulatorSkeletonItem />
              <SimulatorSkeletonItem />
            </>
          </ShowComponent>
        </ShowComponent>
      </List>
    </Box>
  );
};

SimulatorPopoverChild.propTypes = {};

const SimulatorPopover = ({ open, onClose, anchor }) => {
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
      <SimulatorPopoverChild />
    </Popover>
  );
};

SimulatorPopover.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  anchor: PropTypes.object,
};

export default SimulatorPopover;
