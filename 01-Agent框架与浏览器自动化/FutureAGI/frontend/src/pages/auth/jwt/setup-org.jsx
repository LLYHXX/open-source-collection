import React from "react";
import { Helmet } from "react-helmet-async";
import SetupOrg from "src/sections/auth/jwt/setup-org";

// ----------------------------------------------------------------------

export default function SetupOrgPage() {
  return (
    <>
      <Helmet>
        <title>Setup Organization</title>
      </Helmet>

      <SetupOrg />
    </>
  );
}
