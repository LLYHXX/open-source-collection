import { Box, Typography } from "@mui/material";
import React, { useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router";
import { useEvaluationList } from "src/api/develop/develop-detail";
import BackButton from "src/sections/develop-detail/Common/BackButton";
import CustomBreadcrumbs from "src/components/custom-breadcrumbs";

const EvalsSelectRow = () => {
  const navigate = useNavigate();
  const { evalId } = useParams();

  const { data: evalsList, refetch: refetchData } = useEvaluationList();

  useEffect(() => {
    refetchData();
  }, [evalId]);

  // const evaluationOptions = useMemo(
  //   () =>
  //     evalsList?.map(({ id, name }) => ({
  //       label: name,
  //       value: id,
  //     })),
  //   [evalsList],
  // );

  const handleBackClick = () => {
    if (window.history.state?.idx > 0) {
      navigate(-1);
    } else {
      navigate(`/dashboard/evaluations`);
    }
  };

  const { links, currentEvals } = useMemo(() => {
    const currentEvals =
      evalsList?.find((evalItem) => evalItem.id === evalId) || {};
    const links = [
      {
        name: "Usage",
        href: "/dashboard/evaluations/usage",
      },
      {
        name: currentEvals?.name || "",
        href: `/dashboard/evaluations/${currentEvals.id}`,
      },
    ];

    return { links, currentEvals };
  }, [evalsList]);

  return (
    <Box display="flex" flexDirection="column" gap="16px">
      <Box
        sx={{
          display: "flex",
          gap: 2,
          alignItems: "center",
        }}
      >
        <BackButton onBack={handleBackClick} />
        <CustomBreadcrumbs links={links} />
      </Box>
      <Box sx={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {currentEvals?.name && (
          <Typography
            variant="m3"
            fontWeight={"fontWeightSemiBold"}
            color="text.primary"
          >
            {currentEvals?.name}
          </Typography>
        )}
        {currentEvals.description && (
          <Typography
            variant="s1"
            fontWeight={"fontWeightRegular"}
            color="text.primary"
          >
            {currentEvals?.description || ""}
          </Typography>
        )}
      </Box>
    </Box>
  );
};

EvalsSelectRow.propTypes = {};

export default EvalsSelectRow;
