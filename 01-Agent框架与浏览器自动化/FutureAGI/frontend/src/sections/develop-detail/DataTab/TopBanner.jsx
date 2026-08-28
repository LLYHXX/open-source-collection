import React, { useEffect, useState } from "react";
import UploadProgressNotification from "./DevelopDataNotificationBar";
import { ShowComponent } from "src/components/show";
import { useQuery } from "@tanstack/react-query";

const TopBanner = () => {
  const [notificationData, setNotificationData] = useState([]);
  const [showProgressBar, setShowProgressBar] = useState(false);

  const { data } = useQuery({
    queryKey: ["develop-data"],
    enabled: false,
  });

  useEffect(() => {
    const metaData = data?.result?.metadata;
    setNotificationData(metaData);
    setShowProgressBar(!data?.result?.datasetConfig?.dismissBanner);
  }, [data]);

  return (
    <ShowComponent
      condition={
        showProgressBar && notificationData && notificationData?.status
      }
    >
      <UploadProgressNotification
        showReason={
          notificationData?.status?.datasetStatus == "PartialDataExtracted"
        }
        status={notificationData?.status}
        onClose={() => setShowProgressBar(false)}
      />
    </ShowComponent>
  );
};

export default TopBanner;
