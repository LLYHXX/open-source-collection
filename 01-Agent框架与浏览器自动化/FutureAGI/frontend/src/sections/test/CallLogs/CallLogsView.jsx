import { Box, Button } from "@mui/material";
import React, { useMemo, useState } from "react";
import CallLogsHeader from "./CallLogsHeader";
import CallLogsCard from "./CallLogsCard";
import { AudioPlaybackProvider } from "src/components/custom-audio/context-provider/AudioPlaybackContext";
import { useScrollEnd } from "../../../hooks/use-scroll-end";
import { useInfiniteQuery } from "@tanstack/react-query";
import axios from "../../../utils/axios";
import { endpoints } from "../../../utils/axios";
import { useNavigate, useParams } from "react-router";
import { useDebounce } from "src/hooks/use-debounce";
import { ShowComponent } from "src/components/show";
import EmptyLayout from "src/components/EmptyLayout/EmptyLayout";
import { PERMISSIONS, RolePermission } from "src/utils/rolePermissionMapping";
import { useAuthContext } from "src/auth/hooks";

const CallLogsView = () => {
  const { testId } = useParams();
  const [searchText, setSearchText] = useState("");
  const { role } = useAuthContext();
  const navigate = useNavigate();

  const debouncedSearchText = useDebounce(searchText, 500);

  const { data, isFetchingNextPage, fetchNextPage, isPending } =
    useInfiniteQuery({
      queryFn: ({ pageParam }) =>
        axios.get(endpoints.runTests.callExecutionsByTestRunId(testId), {
          params: { page: pageParam, search: debouncedSearchText },
        }),
      queryKey: ["test-runs-call-logs", testId, debouncedSearchText],
      getNextPageParam: ({ data }) =>
        data?.next ? data?.current_page + 1 : null,
      initialPageParam: 1,
    });
  const callLogs = useMemo(
    () => data?.pages.flatMap((page) => page.data.results),
    [data],
  );

  const scrollContainer = useScrollEnd(() => {
    if (isPending || isFetchingNextPage) return;
    fetchNextPage();
  }, [fetchNextPage, isFetchingNextPage, isPending]);

  return (
    <Box
      sx={{
        padding: 2,
        display: "flex",
        flexDirection: "column",
        gap: 2,
        height: "100%",
      }}
    >
      <CallLogsHeader searchText={searchText} setSearchText={setSearchText} />
      <ShowComponent
        condition={
          !isPending && callLogs.length === 0 && debouncedSearchText === ""
        }
      >
        <EmptyLayout
          title="No Call Logs Found"
          description="Get started by running a test"
          action={
            <Button
              variant="contained"
              onClick={() => {
                navigate(`/dashboard/simulate/test/${testId}/runs`);
              }}
              sx={{
                bgcolor: "primary.main",
                "&:hover": {
                  bgcolor: "primary.dark",
                },
              }}
              disabled={
                !RolePermission.SIMULATION_AGENT[PERMISSIONS.CREATE][role]
              }
            >
              Run New Test
            </Button>
          }
          hideIcon
        />
      </ShowComponent>

      <AudioPlaybackProvider>
        <Box
          ref={scrollContainer}
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            overflowY: "auto",
          }}
        >
          {callLogs?.map((item) => (
            <CallLogsCard key={item.id} log={item} />
          ))}
        </Box>
      </AudioPlaybackProvider>
    </Box>
  );
};

export default CallLogsView;
