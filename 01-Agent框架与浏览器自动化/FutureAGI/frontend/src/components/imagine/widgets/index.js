import WidgetBarChart from "./WidgetBarChart";
import WidgetLineChart from "./WidgetLineChart";
import WidgetAreaChart from "./WidgetAreaChart";
import WidgetPieChart from "./WidgetPieChart";
import WidgetDonutChart from "./WidgetDonutChart";
import WidgetHeatmap from "./WidgetHeatmap";
import WidgetRadarChart from "./WidgetRadarChart";
import WidgetMetricCard from "./WidgetMetricCard";
import WidgetKeyValue from "./WidgetKeyValue";
import WidgetMarkdown from "./WidgetMarkdown";
import WidgetCodeBlock from "./WidgetCodeBlock";
import WidgetDataTable from "./WidgetDataTable";
import WidgetJsonTree from "./WidgetJsonTree";
import WidgetTimeline from "./WidgetTimeline";
import WidgetAgentGraph from "./WidgetAgentGraph";
import WidgetSpanTree from "./WidgetSpanTree";
import WidgetScreenshot from "./WidgetScreenshot";

/**
 * Widget Registry — maps widget type strings to React components.
 * Each component receives: { config, traceData? }
 */
const WIDGET_REGISTRY = {
  bar_chart: WidgetBarChart,
  line_chart: WidgetLineChart,
  area_chart: WidgetAreaChart,
  pie_chart: WidgetPieChart,
  donut_chart: WidgetDonutChart,
  heatmap: WidgetHeatmap,
  radar_chart: WidgetRadarChart,
  metric_card: WidgetMetricCard,
  key_value: WidgetKeyValue,
  markdown: WidgetMarkdown,
  code_block: WidgetCodeBlock,
  data_table: WidgetDataTable,
  json_tree: WidgetJsonTree,
  timeline: WidgetTimeline,
  agent_graph: WidgetAgentGraph,
  span_tree: WidgetSpanTree,
  screenshot_annotated: WidgetScreenshot,
};

export default WIDGET_REGISTRY;
