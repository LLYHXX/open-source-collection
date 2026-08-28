import { Box } from "@mui/material";
import React, { useEffect, useState } from "react";
import UserHeaderSection from "./UserHeaderSection";
import UserSummaryCardsSection from "./UserSummaryCardsSection";
import UserMetricsGraphSection from "./UserMetricsGraphSection";
import { useUrlState } from "src/routes/hooks/use-url-state";
import UserTraceSessionSection from "./UserTraceSessionSection";
import { DEFAULT_DATE_FILTER } from "../common";
import { Helmet } from "react-helmet-async";
import ProjectBreadCrumbs from "src/sections/project-detail/ProjectBreadCrumbs";
import { useParams } from "react-router";
import { useTraceSessionStoreShallow } from "../Store/useTraceSessionStore";

const UserDetails = () => {
  const { userId: selectedUserId } = useParams();
  const { observeId } = useParams();
  const [dateFilter, setDateFilter] = useUrlState(
    "dateFilter",
    DEFAULT_DATE_FILTER,
  );
  const [lastActiveDate, setLastActiveDate] = useState(null);
  const { setCellHeight } = useTraceSessionStoreShallow((s) => ({
    setCellHeight: s.setCellHeight,
  }));

  useEffect(() => {
    return () => {
      setCellHeight("Short");
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <Helmet>
        <title>User Details</title>
      </Helmet>
      <Box
        display="flex"
        flexDirection="column"
        height="100%"
        bgcolor={"background.paper"}
      >
        {/* Sticky Header */}
        <Box
          sx={{
            position: "sticky",
            top: 0,
          }}
        >
          {!observeId && (
            <Box p={1.5}>
              <ProjectBreadCrumbs
                links={[
                  {
                    name: "All Users",
                    href: "/dashboard/users",
                  },
                  {
                    name: selectedUserId,
                    href: `/dashboard/users/${selectedUserId}`,
                  },
                ]}
              />
            </Box>
          )}
          <UserHeaderSection
            dateFilter={dateFilter}
            setDateFilter={setDateFilter}
            isEdit={false}
            lastActiveDate={lastActiveDate}
          />
        </Box>

        {/* Scrollable Content */}
        <Box
          sx={{
            overflowY: "auto",
            flex: 1,
          }}
        >
          <Box
            sx={{
              pr: 3,
              px: 2,
              py: 1,
              display: "flex",
              flexDirection: "column",
              gap: 2,
            }}
          >
            <UserSummaryCardsSection setLastActiveDate={setLastActiveDate} />
          </Box>
          <Box sx={{ p: 2 }}>
            <UserMetricsGraphSection />
          </Box>
          <Box sx={{ p: 1 }}>
            <UserTraceSessionSection />
          </Box>
        </Box>
      </Box>
    </>
  );
};

export default UserDetails;
