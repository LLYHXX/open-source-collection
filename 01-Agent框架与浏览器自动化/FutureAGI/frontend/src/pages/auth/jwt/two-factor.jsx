import React from "react";
import { Helmet } from "react-helmet-async";

import TwoFactorVerifyView from "src/sections/auth/jwt/two-factor-verify-view";

// ----------------------------------------------------------------------

export default function TwoFactorPage() {
  return (
    <>
      <Helmet>
        <title>Two-Factor Authentication</title>
      </Helmet>

      <TwoFactorVerifyView />
    </>
  );
}
