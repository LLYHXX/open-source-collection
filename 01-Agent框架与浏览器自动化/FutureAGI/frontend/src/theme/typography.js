// ----------------------------------------------------------------------

export function remToPx(value) {
  return Math.round(parseFloat(value) * 16);
}

export function pxToRem(value) {
  return `${value / 16}rem`;
}

export function responsiveFontSizes({ sm, md, lg }) {
  return {
    "@media (min-width:600px)": {
      fontSize: pxToRem(sm),
    },
    "@media (min-width:900px)": {
      fontSize: pxToRem(md),
    },
    "@media (min-width:1200px)": {
      fontSize: pxToRem(lg),
    },
  };
}

export const primaryFont = "Inter, sans-serif";
export const secondaryFont = "Inter, sans-serif";

// ----------------------------------------------------------------------

export const typography = {
  fontFamily: primaryFont,
  fontSecondaryFamily: secondaryFont,
  fontWeightRegular: 400,
  fontWeightMedium: 500,
  fontWeightSemiBold: 600,
  fontWeightBold: 700,
  h1: {
    fontWeight: 800,
    lineHeight: 80 / 64,
    fontSize: pxToRem(40),
    ...responsiveFontSizes({ sm: 52, md: 58, lg: 64 }),
  },
  h2: {
    fontWeight: 800,
    lineHeight: 64 / 48,
    fontSize: pxToRem(32),
    ...responsiveFontSizes({ sm: 40, md: 44, lg: 48 }),
  },
  h3: {
    fontWeight: 700,
    lineHeight: 1.5,
    fontSize: pxToRem(24),
    ...responsiveFontSizes({ sm: 26, md: 30, lg: 32 }),
  },
  h4: {
    fontWeight: 700,
    lineHeight: 1.5,
    fontSize: pxToRem(20),
    ...responsiveFontSizes({ sm: 20, md: 24, lg: 24 }),
  },
  h5: {
    fontWeight: 700,
    lineHeight: 1.5,
    fontSize: pxToRem(18),
    ...responsiveFontSizes({ sm: 19, md: 20, lg: 20 }),
  },
  h6: {
    fontWeight: 700,
    lineHeight: 28 / 18,
    fontSize: pxToRem(17),
    ...responsiveFontSizes({ sm: 18, md: 18, lg: 18 }),
  },
  subtitle1: {
    fontWeight: 600,
    lineHeight: 1.5,
    fontSize: pxToRem(16),
  },
  subtitle2: {
    fontWeight: 600,
    lineHeight: 22 / 14,
    fontSize: pxToRem(14),
  },
  subheader: {
    fontWeight: 700,
    fontSize: pxToRem(11),
    lineHeight: "1.6",
  },
  body1: {
    lineHeight: 1.5,
    fontSize: pxToRem(16),
  },
  body2: {
    lineHeight: 22 / 14,
    fontSize: pxToRem(14),
  },
  caption: {
    lineHeight: 1.5,
    fontSize: pxToRem(12),
  },
  overline: {
    fontWeight: 700,
    lineHeight: 1.5,
    fontSize: pxToRem(12),
    textTransform: "uppercase",
  },
  button: {
    fontWeight: 600,
    lineHeight: 24 / 14,
    fontSize: pxToRem(15),
    textTransform: "unset",
  },
  s1: {
    fontSize: pxToRem(14),
    lineHeight: "22px",
  },
  s1_2: {
    fontSize: pxToRem(15),
    lineHeight: "22px",
  },
  s2: {
    fontSize: pxToRem(12),
    lineHeight: "18px",
  },
  s2_1: {
    fontSize: pxToRem(13),
    lineHeight: "20px",
  },
  s3: {
    fontSize: pxToRem(11),
    lineHeight: "16px",
  },
  m1: {
    fontSize: pxToRem(20),
    lineHeight: "34px",
  },
  m2: {
    fontSize: pxToRem(18),
    lineHeight: "28px",
  },
  m3: {
    fontSize: pxToRem(16),
    lineHeight: "24px",
  },
  l1: {
    fontSize: pxToRem(32),
    lineHeight: "48px",
  },
  l2: {
    fontSize: pxToRem(28),
    lineHeight: "42px",
  },
  l3: {
    fontSize: pxToRem(24),
    lineHeight: "36px",
  },
};
