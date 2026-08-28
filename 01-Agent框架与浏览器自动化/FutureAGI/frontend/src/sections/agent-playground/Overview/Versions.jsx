import React, { useCallback, useMemo } from "react";
import { Box } from "@mui/material";
import PropTypes from "prop-types";
import { useScrollEnd } from "src/hooks/use-scroll-end";
import VersionList from "src/components/VersionList/VersionList";
import { useAgentPlaygroundStoreShallow } from "../store";
import { useGetGraphVersions } from "src/api/agent-playground/agent-playground";
import { VERSION_STATUS } from "../utils/constants";

const Versions = ({ selectedVersion, onVersionChange }) => {
  const { currentAgent } = useAgentPlaygroundStoreShallow((s) => ({
    currentAgent: s.currentAgent,
  }));

  const { data, isLoading, isFetchingNextPage, fetchNextPage, hasNextPage } =
    useGetGraphVersions(currentAgent?.id);

  const versions = useMemo(
    () =>
      (data?.pages ?? []).flatMap((page) =>
        (page.data?.result?.versions ?? []).map((v) => ({
          id: v.id,
          versionNameDisplay: String(v.version_number),
          created_at: v.created_at,
          commitMessage: v.commit_message ?? v.commitMessage ?? "",
          status: v.status,
          isDraft: v.status === VERSION_STATUS.DRAFT,
        })),
      ),
    [data],
  );

  const fetchNext = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const scrollContainerRef = useScrollEnd(fetchNext, [fetchNext]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        overflowX: "hidden",
      }}
    >
      <VersionList
        versions={versions}
        selectedVersion={selectedVersion}
        onVersionChange={onVersionChange}
        isLoading={isLoading}
        isFetchingNextVersions={isFetchingNextPage}
        scrollContainerRef={scrollContainerRef}
        sx={{
          px: 0,
        }}
      />
    </Box>
  );
};

Versions.propTypes = {
  selectedVersion: PropTypes.string,
  onVersionChange: PropTypes.func,
};

Versions.defaultProps = {
  selectedVersion: null,
  onVersionChange: () => {},
};

export default Versions;
