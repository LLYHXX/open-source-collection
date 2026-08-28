import {
  Box,
  Button,
  Chip,
  IconButton,
  Typography,
  useTheme,
} from "@mui/material";
import { format } from "date-fns";
import React from "react";
import Iconify from "../iconify";
import CallStatus from "src/sections/test/CallLogs/CallStatus";
import { handleOnDocsClicked } from "src/utils/Mixpanel";
import SvgColor from "../svg-color";
import PropTypes from "prop-types";
import { LoadingButton } from "@mui/lab";
import { copyToClipboard } from "src/utils/utils";
import { enqueueSnackbar } from "notistack";
import { AGENT_TYPES } from "src/sections/agents/constants";
import { getCsatScoreColor } from "./common";

export const formatDurationSafe = (duration) => {
  if (duration === null || duration === undefined || isNaN(duration))
    return "-";

  const totalSeconds = Number(duration);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (seconds > 0 || parts.length === 0) parts.push(`${seconds.toFixed(2)}s`);

  return parts.join(" ");
};

const CustomCallLogHeader = ({
  rowIndex,
  isFetching,
  totalCount,
  onPrevClick,
  onNextClick,
  phoneNumber,
  scenario,
  timestamp,
  duration,
  status,
  onClose,
  module,
  type,
  endedReason,
  overAllScore,
  serviceProviderCallId,
  customerCallId,
  simulationCallType,
  onAnnotate,
}) => {
  const theme = useTheme();
  const Separator = () => (
    <Typography
      typography="s2_1"
      color="text.disabled"
      fontWeight="fontWeightRegular"
      sx={{ mx: 0.5 }}
    >
      |
    </Typography>
  );
  const typeKey = (type ?? "").toLowerCase();
  const isInbound = typeKey.includes("inbound");
  const callTypeLabel = isInbound ? "Inbound" : "Outbound";
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        justifyContent: "space-between",
        borderBottom: "1px solid",
        borderColor: "divider",
        py: 2,
        position: "sticky",
        top: 0,
        zIndex: 1000,
        backgroundColor: "background.paper",
      }}
    >
      {/* LEFT SECTION */}
      <Box
        display="flex"
        flexDirection="column"
        gap={1}
        pl={2}
        sx={{ width: "100%" }}
      >
        <Typography typography="m3" fontWeight="fontWeightSemiBold">
          {simulationCallType === "text"
            ? "Chat Log Details"
            : "Call Log Details"}
        </Typography>

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 0.5,
          }}
        >
          {/* Phone Number */}
          {phoneNumber ? (
            <>
              <Typography
                typography="s2_1"
                color="text.disabled"
                fontWeight="fontWeightRegular"
              >
                {phoneNumber}
              </Typography>
              <Separator />
            </>
          ) : null}

          {/* Scenario */}
          {scenario ? (
            <>
              <Typography
                typography="s2_1"
                color="text.disabled"
                fontWeight="fontWeightRegular"
              >
                {scenario}
              </Typography>
              <Separator />
            </>
          ) : null}

          {timestamp ? (
            <>
              <Typography
                typography="s2_1"
                color="text.disabled"
                fontWeight="fontWeightRegular"
              >
                {format(new Date(timestamp), "yyyy-MM-dd HH:mm:ss")}
              </Typography>
              <Separator />
            </>
          ) : null}

          {duration ? (
            <>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <Iconify
                  icon="material-symbols:schedule-outline"
                  width="14px"
                  height="14px"
                  color="text.disabled"
                />
                <Typography
                  typography="s2_1"
                  color="text.disabled"
                  fontWeight="fontWeightRegular"
                >
                  {formatDurationSafe(duration)}
                </Typography>
              </Box>
              <Separator />
            </>
          ) : null}
          {overAllScore ? (
            <>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <Typography typography="s2_1" fontWeight="fontWeightRegular">
                  CSAT Score:
                </Typography>

                <Typography
                  typography="s2_1"
                  color={getCsatScoreColor(overAllScore)}
                  fontWeight="fontWeightSemiBold"
                >
                  {`${overAllScore}/10`}
                </Typography>
              </Box>

              <Separator />
            </>
          ) : null}

          {type && simulationCallType !== AGENT_TYPES.CHAT ? (
            <>
              <Chip
                label={callTypeLabel}
                variant="medium"
                icon={
                  <SvgColor
                    sx={{ width: 20 }}
                    src={
                      isInbound
                        ? "/assets/icons/ic_call_inbound.svg"
                        : "/assets/icons/ic_call_outbound.svg"
                    }
                  />
                }
                size="small"
                sx={{
                  typography: "s1",
                  fontWeight: "fontWeightMedium",
                  color: "blue.700",
                  bgcolor: "blue.o10",
                  borderRadius: 0.25,
                  paddingX: 1,
                  "& .MuiChip-icon": {
                    color: "blue.700",
                  },
                }}
              />

              <Separator />
            </>
          ) : null}

          <CallStatus value={status ?? ""} />
        </Box>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 0.5,
          }}
        >
          {endedReason && (
            <>
              <Typography
                variant="s2_1"
                color="text.disabled"
                fontWeight={"fontWeightRegular"}
              >
                {simulationCallType === AGENT_TYPES.CHAT ? "Chat" : "Call"} end
                reason : {endedReason}
              </Typography>
              {(serviceProviderCallId || customerCallId) && <Separator />}
            </>
          )}

          {serviceProviderCallId && (
            <>
              <Typography
                variant="s2_1"
                color="text.disabled"
                fontWeight={"fontWeightRegular"}
              >
                Provider Call ID : {serviceProviderCallId}
              </Typography>
              <IconButton
                sx={{
                  paddingY: 0,
                  paddingX: 0.5,
                  height: theme.spacing(3),
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  copyToClipboard(serviceProviderCallId);
                  enqueueSnackbar({
                    message: "Copied to clipboard",
                    variant: "success",
                  });
                }}
              >
                <Iconify
                  icon="tabler:copy"
                  sx={{
                    width: theme.spacing(2),
                    height: theme.spacing(2),
                  }}
                />
              </IconButton>
              {customerCallId && <Separator />}
            </>
          )}

          {customerCallId && (
            <>
              <Typography
                variant="s2_1"
                color="text.disabled"
                fontWeight={"fontWeightRegular"}
              >
                Customer Vapi Call ID : {customerCallId}
              </Typography>
              <IconButton
                sx={{
                  paddingY: 0,
                  paddingX: 0.5,
                  height: theme.spacing(3),
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  copyToClipboard(customerCallId);
                  enqueueSnackbar({
                    message: "Copied to clipboard",
                    variant: "success",
                  });
                }}
              >
                <Iconify
                  icon="tabler:copy"
                  sx={{
                    width: theme.spacing(2),
                    height: theme.spacing(2),
                  }}
                />
              </IconButton>
            </>
          )}
        </Box>
      </Box>

      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          alignSelf: "flex-start",
          gap: 1,
          pr: 2,
        }}
      >
        {onAnnotate && (
          <Button
            variant="soft"
            size="small"
            onClick={onAnnotate}
            startIcon={<Iconify icon="basil:edit-alt-outline" width={16} />}
            sx={{
              color: "text.secondary",
              backgroundColor: "action.hover",
              fontWeight: "fontWeightMedium",
            }}
          >
            Annotate
          </Button>
        )}
        {/* {origin !== "agent-definition" && (
          <> */}
        <LoadingButton
          variant="outlined"
          size="small"
          startIcon={<Iconify icon="akar-icons:chevron-left-small" />}
          sx={{
            padding: "4px 12px",
          }}
          loading={isFetching === "prev"}
          onClick={onPrevClick}
          disabled={isFetching || rowIndex == null || rowIndex <= 0}
        >
          Prev
        </LoadingButton>
        <LoadingButton
          variant="outlined"
          size="small"
          endIcon={<Iconify icon="akar-icons:chevron-right-small" />}
          sx={{
            padding: "4px 12px",
          }}
          onClick={onNextClick}
          loading={isFetching === "next"}
          disabled={
            isFetching ||
            !totalCount ||
            rowIndex == null ||
            rowIndex + 1 >= totalCount
          }
        >
          Next
        </LoadingButton>
        {/* </>
        )} */}

        <Button
          variant="outlined"
          size="small"
          sx={{
            borderRadius: "4px",
            height: "30px",
            px: "4px",
            width: "105px",
          }}
          onClick={() => {
            handleOnDocsClicked(
              `call-log-${module === "simulate" ? "simulate" : "observe"}`,
            );
            window.open(
              "https://docs.futureagi.com/docs/api/run-tests/createruntest",
              "_blank",
            );
          }}
        >
          <SvgColor
            src="/assets/icons/agent/docs.svg"
            sx={{ height: 16, width: 16, mr: 1 }}
          />
          <Typography typography="s2" fontWeight="fontWeightMedium">
            View Docs
          </Typography>
        </Button>

        <IconButton
          onClick={onClose}
          sx={{
            color: "text.primary",
          }}
          size="small"
        >
          <SvgColor
            sx={{
              height: "24px",
              width: "24px",
            }}
            src="/assets/icons/ic_close.svg"
          />
        </IconButton>
      </Box>
    </Box>
  );
};

CustomCallLogHeader.propTypes = {
  isFetching: PropTypes.bool,
  totalCount: PropTypes.bool,
  rowIndex: PropTypes.number,
  phoneNumber: PropTypes.string,
  scenario: PropTypes.string,
  timestamp: PropTypes.string,
  duration: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  status: PropTypes.string,
  onClose: PropTypes.func,
  module: PropTypes.string,
  type: PropTypes.string,
  overAllScore: PropTypes.string,
  serviceProviderCallId: PropTypes.string,
  customerCallId: PropTypes.string,
  endedReason: PropTypes.string,
  onPrevClick: PropTypes.func,
  onNextClick: PropTypes.func,
  origin: PropTypes.string,
  simulationCallType: PropTypes.string,
  onAnnotate: PropTypes.func,
};

export default CustomCallLogHeader;
