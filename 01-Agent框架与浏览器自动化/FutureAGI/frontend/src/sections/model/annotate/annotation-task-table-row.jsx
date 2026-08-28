import React from "react";
import { alpha, useTheme } from "@mui/material/styles";
import {
  Avatar,
  AvatarGroup,
  Divider,
  IconButton,
  MenuItem,
  Stack,
  TableCell,
  TableRow,
  Typography,
  avatarGroupClasses,
  tableCellClasses,
  tableRowClasses,
} from "@mui/material";
import PropTypes from "prop-types";

import { useBoolean } from "src/hooks/use-boolean";
import CustomPopover, { usePopover } from "src/components/custom-popover";
import Iconify from "src/components/iconify";

export default function AnnotationTaskTableRow({ row }) {
  const theme = useTheme();

  const details = useBoolean();
  const popover = usePopover();

  const defaultStyles = {
    borderTop: `solid 1px ${alpha(theme.palette.text.disabled, 0.16)}`,
    borderBottom: `solid 1px ${alpha(theme.palette.text.disabled, 0.16)}`,
    "&:first-of-type": {
      borderTopLeftRadius: 16,
      borderBottomLeftRadius: 16,
      borderLeft: `solid 1px ${alpha(theme.palette.text.disabled, 0.16)}`,
    },
    "&:last-of-type": {
      borderTopRightRadius: 16,
      borderBottomRightRadius: 16,
      borderRight: `solid 1px ${alpha(theme.palette.text.disabled, 0.16)}`,
    },
  };

  function handleClick() {
    throw new Error("Function not implemented.");
  }

  function stringAvatar(name) {
    return {
      sx: {
        bgcolor: stringToColor(name),
      },
      children: `${name.split(" ")[0][0]}${name.split(" ")[1][0]}`,
    };
  }

  function stringToColor(string) {
    let hash = 0;
    let i;

    /* eslint-disable no-bitwise */
    for (i = 0; i < string.length; i += 1) {
      hash = string.charCodeAt(i) + ((hash << 5) - hash);
    }

    let color = "#";

    for (i = 0; i < 3; i += 1) {
      const value = (hash >> (i * 8)) & 0xff;
      color += `00${value.toString(16)}`.slice(-2);
    }
    /* eslint-enable no-bitwise */

    return color;
  }

  return (
    <>
      <TableRow
        // selected={selected}
        sx={{
          borderRadius: 2,
          [`&.${tableRowClasses.selected}, &:hover`]: {
            backgroundColor: "background.paper",
            boxShadow: theme.customShadows.z20,
            transition: theme.transitions.create(
              ["background-color", "box-shadow"],
              {
                duration: theme.transitions.duration.shortest,
              },
            ),
            "&:hover": {
              backgroundColor: "background.paper",
              boxShadow: theme.customShadows.z20,
            },
          },
          [`& .${tableCellClasses.root}`]: {
            ...defaultStyles,
          },
          ...(details.value && {
            [`& .${tableCellClasses.root}`]: {
              ...defaultStyles,
            },
          }),
        }}
      >
        {/* <TableCell padding="checkbox">
          <Checkbox
            checked={selected}
            onDoubleClick={() => console.info('ON DOUBLE CLICK')}
            onClick={onSelectRow}
          />
        </TableCell> */}

        <TableCell onClick={handleClick}>
          <Stack direction="row" alignItems="center" spacing={2}>
            <Typography
              noWrap
              variant="inherit"
              sx={{
                maxWidth: 360,
                cursor: "pointer",
                ...(details.value && { fontWeight: "fontWeightBold" }),
              }}
            >
              {row.taskName}
            </Typography>
          </Stack>
        </TableCell>

        <TableCell onClick={handleClick} sx={{ whiteSpace: "nowrap" }}>
          {row.aiModel.userModelId}
        </TableCell>

        <TableCell
          onClick={handleClick}
          sx={{ whiteSpace: "nowrap" }}
        ></TableCell>

        <TableCell align="right" onClick={handleClick}>
          <AvatarGroup
            max={4}
            sx={{
              display: "inline-flex",
              [`& .${avatarGroupClasses.avatar}`]: {
                width: 24,
                height: 24,
                "&:first-of-type": {
                  fontSize: 12,
                },
              },
            }}
          >
            {row.assignedUsers &&
              row.assignedUsers.map((person) => (
                <Avatar
                  key={person.id}
                  alt={person.name}
                  {...stringAvatar(person.name)}
                  sx={{ bgcolor: "background.neutral" }}
                />
              ))}
          </AvatarGroup>
        </TableCell>

        <TableCell
          align="right"
          sx={{
            px: 1,
            whiteSpace: "nowrap",
          }}
        >
          <IconButton
            color={popover.open ? "inherit" : "default"}
            onClick={popover.onOpen}
          >
            <Iconify icon="eva:more-vertical-fill" />
          </IconButton>
        </TableCell>
      </TableRow>

      <CustomPopover
        open={popover.open}
        onClose={popover.onClose}
        arrow="right-top"
        sx={{ width: 160 }}
      >
        <MenuItem onClick={() => {}}>
          <Iconify icon="eva:link-2-fill" />
          Copy Link
        </MenuItem>

        <MenuItem onClick={() => {}}>
          <Iconify icon="solar:share-bold" />
          Share
        </MenuItem>

        <Divider sx={{ borderStyle: "dashed" }} />

        <MenuItem onClick={() => {}} sx={{ color: "error.main" }}>
          <Iconify icon="solar:trash-bin-trash-bold" />
          Delete
        </MenuItem>
      </CustomPopover>
    </>
  );
}

AnnotationTaskTableRow.propTypes = {
  onDeleteRow: PropTypes.func,
  onSelectRow: PropTypes.func,
  row: PropTypes.object,
  selected: PropTypes.bool,
};
