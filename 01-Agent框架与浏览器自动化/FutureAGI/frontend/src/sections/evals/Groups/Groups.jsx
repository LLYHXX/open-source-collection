import React from "react";
import EvalsWrapper from "../EvalsWrapper";
import GroupsGrid from "./GroupsGrid";

export default function Groups() {
  return (
    <>
      <EvalsWrapper
        containerSx={{
          overflow: "hidden",
        }}
        currentTab="groups"
      >
        <GroupsGrid isEvalsView={true} />
      </EvalsWrapper>
    </>
  );
}
