import React from "react";
import { Helmet } from "react-helmet-async";
import { HeaderComponent } from "src/sections/HeaderComponent";
import ManageTeam from "src/sections/settings/ManageTeam/ManageTeam";

const ManageTeamPage = () => {
  return (
    <>
      <Helmet>
        <title>Settings : Manage Team</title>
      </Helmet>
      <HeaderComponent
        links={[
          {
            name: "Manage Team",
            href: "/",
          },
        ]}
      />
      <ManageTeam />
    </>
  );
};

export default ManageTeamPage;
