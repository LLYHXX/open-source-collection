import React from "react";
import { Helmet } from "react-helmet-async";
import DevKeysView from "src/sections/keys/view/dev-keys-view";

// ----------------------------------------------------------------------

export default function DevKeysPage() {
  return (
    <>
      <Helmet>
        <title>Keys</title>
      </Helmet>
      <DevKeysView />
    </>
  );
}
