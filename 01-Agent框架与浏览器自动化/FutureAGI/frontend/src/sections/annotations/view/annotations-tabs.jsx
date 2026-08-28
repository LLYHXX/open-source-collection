import { Tab, Tabs } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import { useTheme } from "@mui/material/styles";
import { paths } from "src/routes/paths";
import {
  getAnnotationTabSx,
  getAnnotationTabIndicatorProps,
} from "./annotation-tab-styles";

const TABS = [
  { id: "queues", label: "Queues", path: paths.dashboard.annotations.queues },
  { id: "labels", label: "Labels", path: paths.dashboard.annotations.labels },
];

export default function AnnotationsTabs() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();

  const currentTabId =
    TABS.find((t) => pathname.startsWith(t.path))?.id || TABS[0].id;

  // @ts-ignore
  const handleTabChange = (_, newTabId) => {
    const tab = TABS.find((t) => t.id === newTabId);
    if (tab) navigate(tab.path);
  };

  return (
    <Tabs
      value={currentTabId}
      onChange={handleTabChange}
      textColor="primary"
      TabIndicatorProps={getAnnotationTabIndicatorProps(theme)}
      sx={{
        ...getAnnotationTabSx(theme),
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      {TABS.map((tab) => (
        <Tab key={tab.id} label={tab.label} value={tab.id} />
      ))}
    </Tabs>
  );
}
