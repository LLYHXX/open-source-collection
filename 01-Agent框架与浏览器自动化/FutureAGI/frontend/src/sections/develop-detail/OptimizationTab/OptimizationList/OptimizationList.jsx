import { Box, Typography } from "@mui/material";
import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import { useParams } from "react-router";
import axios, { endpoints } from "src/utils/axios";
import OptimizationCard from "./OptimizationCard";
import PropTypes from "prop-types";
import { useScrollEnd } from "src/hooks/use-scroll-end";
import { trackEvent, Events } from "src/utils/Mixpanel";

const OptimizationList = ({
  selectedOptimization,
  setSelectedOptimization,
}) => {
  const { dataset } = useParams();

  const { data, fetchNextPage, isLoading, isFetchingNextPage } =
    useInfiniteQuery({
      queryFn: () =>
        axios.get(endpoints.develop.optimizeDevelop.list, {
          params: { dataset_id: dataset },
        }),
      queryKey: ["develop-optimization-list", dataset],
      initialPageParam: 1,
      getNextPageParam: ({ data }) => {
        return data?.next ? data.current_page + 1 : null;
      },
    });

  const optimizationList = data?.pages
    ? data.pages.flatMap((page) => page.data.results)
    : [];
  const scrollContainerRef = useScrollEnd(() => {
    if (isFetchingNextPage || isLoading) return;
    fetchNextPage();
  }, [isFetchingNextPage, isLoading]);

  return (
    <Box
      sx={{
        maxWidth: "45%",
        width: "39%",
        display: "flex",
        gap: 2,
        flexDirection: "column",
        overflowY: "auto",
      }}
      ref={scrollContainerRef}
    >
      <Box
        sx={{
          paddingX: 2,
          paddingTop: 2,
          position: "sticky",
          top: 0,
          backgroundColor: "background.paper",
        }}
      >
        <Typography fontWeight={600} fontSize="12px">
          Optimization runs: {data?.pages[0]?.data?.count}
        </Typography>
      </Box>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 1,
          paddingX: 2,
        }}
      >
        {optimizationList?.map((optimization) => (
          <OptimizationCard
            selected={selectedOptimization?.id === optimization.id}
            onClick={() => {
              setSelectedOptimization(optimization);
              trackEvent(Events.optDatasetSelect, {
                id: optimization.id,
                name: optimization.name,
                model: optimization.modelConfig,
              });
            }}
            key={optimization.id}
            optimization={optimization}
          />
        ))}
      </Box>
    </Box>
  );
};

OptimizationList.propTypes = {
  selectedOptimization: PropTypes.object,
  setSelectedOptimization: PropTypes.func,
};

export default OptimizationList;
