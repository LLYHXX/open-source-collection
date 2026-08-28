import React from "react";
import PropTypes from "prop-types";
import { Box, Typography, styled, Skeleton } from "@mui/material";
import { RouterLink } from "src/routes/components";
import Link from "@mui/material/Link";
import SvgColor from "../../components/svg-color";

// ----------------------------------------------------------------------

const BreadcrumbContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  gap: theme.spacing(0.5),
  flexWrap: "wrap",
}));

const BreadcrumbSeparator = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.primary,
  userSelect: "none",
  display: "inline-flex",
  alignItems: "center",
  marginX: "10px",
}));

const BreadcrumbLink = styled(Link)(({ theme, isActive: _isActive }) => ({
  textDecoration: "none",
  color: theme.palette.text.disabled,
  typography: "s1",
  fontWeight: theme.typography.fontWeightMedium,
  transition: "color 0.2s ease",
}));

const BreadcrumbText = styled(Typography)(({ theme, isActive }) => ({
  color: isActive ? theme.palette.text.primary : theme.palette.text.disabled,
  typography: "s1",
  fontWeight: theme.typography.fontWeightMedium,
}));

// ----------------------------------------------------------------------

export default function TestDetailBreadcrumb({ items, sx, ...other }) {
  if (!items || !Array.isArray(items) || items.length === 0) {
    return null;
  }

  return (
    <BreadcrumbContainer sx={sx} {...other}>
      {items?.map((item, index) => {
        const isLast = index === items.length - 1;
        const isActive = isLast;
        const isLoading = item.isLoading;

        return (
          <React.Fragment key={item.key || index}>
            {isLoading ? (
              <Skeleton
                variant="text"
                width={100}
                height={30}
                sx={{ typography: "s1" }}
              />
            ) : item.href && !isLast ? (
              <BreadcrumbLink
                component={RouterLink}
                href={item.href}
                isActive={isActive}
                onClick={item.onClick}
              >
                {item.label}
              </BreadcrumbLink>
            ) : (
              <BreadcrumbText isActive={isActive}>{item.label}</BreadcrumbText>
            )}
            {!isLast && (
              <BreadcrumbSeparator component="span">
                <SvgColor
                  src="/assets/icons/custom/lucide--chevron-right.svg"
                  sx={{ width: "20px", height: "20px" }}
                  color="text.primary"
                />
              </BreadcrumbSeparator>
            )}
          </React.Fragment>
        );
      })}
    </BreadcrumbContainer>
  );
}

TestDetailBreadcrumb.propTypes = {
  items: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      label: PropTypes.string.isRequired,
      href: PropTypes.string,
      onClick: PropTypes.func,
      separator: PropTypes.string,
      isLoading: PropTypes.bool,
    }),
  ).isRequired,
  sx: PropTypes.object,
};
