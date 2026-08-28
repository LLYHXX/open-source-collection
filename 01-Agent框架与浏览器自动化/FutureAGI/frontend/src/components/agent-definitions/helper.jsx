import { Box } from "@mui/material";
// import { AgentActionMenu } from "./AgentActionMenu";
import AgentNameCellRenderer from "./CustomCellRenderers/AgentNameCellRenderer";
import ChipCellRenderer from "src/components/scenarios/CustomCellRenderers/ChipCellRenderer";
// import { PERMISSIONS, RolePermission } from "src/utils/rolePermissionMapping";
import { camelCaseToTitleCase } from "src/utils/utils";
import { AGENT_TYPES } from "src/sections/agents/constants";

export const languageMap = {
  ar: "Arabic",
  bg: "Bulgarian",
  zh: "Chinese",
  cs: "Czech",
  da: "Danish",
  nl: "Dutch",
  en: "English",
  fi: "Finnish",
  fr: "French",
  de: "German",
  el: "Greek",
  hi: "Hindi",
  hu: "Hungarian",
  id: "Indonesian",
  it: "Italian",
  ja: "Japanese",
  ko: "Korean",
  ms: "Malay",
  no: "Norwegian",
  pl: "Polish",
  pt: "Portuguese",
  ro: "Romanian",
  ru: "Russian",
  sk: "Slovak",
  es: "Spanish",
  sv: "Swedish",
  tr: "Turkish",
  uk: "Ukrainian",
  vi: "Vietnamese",
};

export const languageOptions = [
  { value: "ar", label: "Arabic" },
  { value: "bg", label: "Bulgarian" },
  { value: "zh", label: "Chinese Simplified" },
  { value: "cs", label: "Czech" },
  { value: "da", label: "Danish" },
  { value: "nl", label: "Dutch" },
  { value: "en", label: "English" },
  { value: "fi", label: "Finnish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "el", label: "Greek" },
  { value: "hi", label: "Hindi" },
  { value: "hu", label: "Hungarian" },
  { value: "id", label: "Indonesian" },
  { value: "it", label: "Italian" },
  { value: "ja", label: "Japanese" },
  { value: "ko", label: "Korean" },
  { value: "ms", label: "Malay" },
  { value: "no", label: "Norwegian" },
  { value: "pl", label: "Polish" },
  { value: "pt", label: "Portuguese" },
  { value: "ro", label: "Romanian" },
  { value: "ru", label: "Russian" },
  { value: "sk", label: "Slovak" },
  { value: "es", label: "Spanish" },
  { value: "sv", label: "Swedish" },
  { value: "tr", label: "Turkish" },
  { value: "uk", label: "Ukrainian" },
  { value: "vi", label: "Vietnamese" },
];

export const pinCodeOptions = [
  {
    label: "United States",
    value: "1",
    countryFlag: "https://flagcdn.com/us.svg",
  },
  { label: "Canada", value: "1", countryFlag: "https://flagcdn.com/ca.svg" },
  {
    label: "United Kingdom",
    value: "44",
    countryFlag: "https://flagcdn.com/gb.svg",
  },
  { label: "India", value: "91", countryFlag: "https://flagcdn.com/in.svg" },
  {
    label: "Australia",
    value: "61",
    countryFlag: "https://flagcdn.com/au.svg",
  },
  { label: "Germany", value: "49", countryFlag: "https://flagcdn.com/de.svg" },
  { label: "France", value: "33", countryFlag: "https://flagcdn.com/fr.svg" },
  { label: "Italy", value: "39", countryFlag: "https://flagcdn.com/it.svg" },
  { label: "Spain", value: "34", countryFlag: "https://flagcdn.com/es.svg" },
  {
    label: "Netherlands",
    value: "31",
    countryFlag: "https://flagcdn.com/nl.svg",
  },
  { label: "Sweden", value: "46", countryFlag: "https://flagcdn.com/se.svg" },
  { label: "Norway", value: "47", countryFlag: "https://flagcdn.com/no.svg" },
  { label: "Denmark", value: "45", countryFlag: "https://flagcdn.com/dk.svg" },
  {
    label: "Switzerland",
    value: "41",
    countryFlag: "https://flagcdn.com/ch.svg",
  },
  { label: "Belgium", value: "32", countryFlag: "https://flagcdn.com/be.svg" },
  { label: "Austria", value: "43", countryFlag: "https://flagcdn.com/at.svg" },
  { label: "Finland", value: "358", countryFlag: "https://flagcdn.com/fi.svg" },
  { label: "Ireland", value: "353", countryFlag: "https://flagcdn.com/ie.svg" },
  {
    label: "Portugal",
    value: "351",
    countryFlag: "https://flagcdn.com/pt.svg",
  },
  { label: "Greece", value: "30", countryFlag: "https://flagcdn.com/gr.svg" },
  { label: "Poland", value: "48", countryFlag: "https://flagcdn.com/pl.svg" },
  {
    label: "Czech Republic",
    value: "420",
    countryFlag: "https://flagcdn.com/cz.svg",
  },
  { label: "Hungary", value: "36", countryFlag: "https://flagcdn.com/hu.svg" },
  { label: "Romania", value: "40", countryFlag: "https://flagcdn.com/ro.svg" },
  { label: "Russia", value: "7", countryFlag: "https://flagcdn.com/ru.svg" },
  { label: "Ukraine", value: "380", countryFlag: "https://flagcdn.com/ua.svg" },
  { label: "Turkey", value: "90", countryFlag: "https://flagcdn.com/tr.svg" },
  {
    label: "Saudi Arabia",
    value: "966",
    countryFlag: "https://flagcdn.com/sa.svg",
  },
  {
    label: "United Arab Emirates",
    value: "971",
    countryFlag: "https://flagcdn.com/ae.svg",
  },
  { label: "Qatar", value: "974", countryFlag: "https://flagcdn.com/qa.svg" },
  { label: "Kuwait", value: "965", countryFlag: "https://flagcdn.com/kw.svg" },
  { label: "Oman", value: "968", countryFlag: "https://flagcdn.com/om.svg" },
  { label: "Bahrain", value: "973", countryFlag: "https://flagcdn.com/bh.svg" },
  { label: "Pakistan", value: "92", countryFlag: "https://flagcdn.com/pk.svg" },
  {
    label: "Bangladesh",
    value: "880",
    countryFlag: "https://flagcdn.com/bd.svg",
  },
  {
    label: "Sri Lanka",
    value: "94",
    countryFlag: "https://flagcdn.com/lk.svg",
  },
  { label: "Nepal", value: "977", countryFlag: "https://flagcdn.com/np.svg" },
  { label: "Bhutan", value: "975", countryFlag: "https://flagcdn.com/bt.svg" },
  { label: "China", value: "86", countryFlag: "https://flagcdn.com/cn.svg" },
  { label: "Japan", value: "81", countryFlag: "https://flagcdn.com/jp.svg" },
  {
    label: "South Korea",
    value: "82",
    countryFlag: "https://flagcdn.com/kr.svg",
  },
  { label: "Taiwan", value: "886", countryFlag: "https://flagcdn.com/tw.svg" },
  {
    label: "Hong Kong",
    value: "852",
    countryFlag: "https://flagcdn.com/hk.svg",
  },
  {
    label: "Singapore",
    value: "65",
    countryFlag: "https://flagcdn.com/sg.svg",
  },
  { label: "Malaysia", value: "60", countryFlag: "https://flagcdn.com/my.svg" },
  {
    label: "Indonesia",
    value: "62",
    countryFlag: "https://flagcdn.com/id.svg",
  },
  { label: "Thailand", value: "66", countryFlag: "https://flagcdn.com/th.svg" },
  { label: "Vietnam", value: "84", countryFlag: "https://flagcdn.com/vn.svg" },
  {
    label: "Philippines",
    value: "63",
    countryFlag: "https://flagcdn.com/ph.svg",
  },
  {
    label: "New Zealand",
    value: "64",
    countryFlag: "https://flagcdn.com/nz.svg",
  },
  {
    label: "South Africa",
    value: "27",
    countryFlag: "https://flagcdn.com/za.svg",
  },
  { label: "Nigeria", value: "234", countryFlag: "https://flagcdn.com/ng.svg" },
  { label: "Kenya", value: "254", countryFlag: "https://flagcdn.com/ke.svg" },
  { label: "Egypt", value: "20", countryFlag: "https://flagcdn.com/eg.svg" },
  { label: "Morocco", value: "212", countryFlag: "https://flagcdn.com/ma.svg" },
  { label: "Brazil", value: "55", countryFlag: "https://flagcdn.com/br.svg" },
  { label: "Mexico", value: "52", countryFlag: "https://flagcdn.com/mx.svg" },
  {
    label: "Argentina",
    value: "54",
    countryFlag: "https://flagcdn.com/ar.svg",
  },
  { label: "Chile", value: "56", countryFlag: "https://flagcdn.com/cl.svg" },
  { label: "Colombia", value: "57", countryFlag: "https://flagcdn.com/co.svg" },
  { label: "Peru", value: "51", countryFlag: "https://flagcdn.com/pe.svg" },
  {
    label: "Venezuela",
    value: "58",
    countryFlag: "https://flagcdn.com/ve.svg",
  },
];

export const getAgentColumnDefs = (_role) => [
  {
    headerName: "Agent Name",
    field: "agent_name",
    minWidth: 300,
    flex: 2,
    cellRenderer: AgentNameCellRenderer,
  },
  {
    headerName: "Type",
    field: "inbound",
    flex: 0.7,
    cellRenderer: ChipCellRenderer,
    cellRendererParams: {
      resolveKey: (data) =>
        data.agentType === AGENT_TYPES.VOICE
          ? data.inbound
            ? "voice_inbound"
            : "voice_outbound"
          : "chat",
    },
  },
  {
    headerName: "Provider",
    field: "provider",
    flex: 0.7,
    cellRenderer: ({ value }) => (
      <Box height={"100%"} display={"flex"} alignItems={"center"}>
        {value ? camelCaseToTitleCase(value) : "-"}
      </Box>
    ),
  },
  {
    headerName: "Contact Number",
    field: "contact_number",
    flex: 1,
    cellRenderer: (params) => {
      const { value, data } = params;
      return (
        <Box height="100%" display="flex" alignItems="center">
          {data?.agentType === AGENT_TYPES.CHAT ? "NA" : value}
        </Box>
      );
    },
  },

  {
    headerName: "Languages",
    field: "languages",
    flex: 0.7,
    cellRenderer: ({ value }) => {
      if (!value || !Array.isArray(value) || value.length === 0) return null;

      const maxVisible = 2;
      const visibleLanguages = value
        .slice(0, maxVisible)
        .map((lang) => languageMap[lang] || lang);
      const remainingCount = value.length - maxVisible;

      return (
        <Box
          sx={{
            display: "flex",
            height: "100%",
            alignItems: "center",
          }}
        >
          {visibleLanguages.join(", ")}
          {remainingCount > 0 && `, +${remainingCount}`}
        </Box>
      );
    },
  },
  {
    headerName: "Version",
    field: "latest_version",
    flex: 0.7,
    cellRenderer: ({ value }) => (
      <Box height={"100%"} display={"flex"} alignItems={"center"}>
        {value ? `v${value}` : "-"}
      </Box>
    ),
  },
  // ...(RolePermission.SIMULATION_AGENT[PERMISSIONS.UPDATE][role] &&
  // RolePermission.SIMULATION_AGENT[PERMISSIONS.DELETE][role]
  //   ? [
  //       {
  //         headerName: "",
  //         field: "actions",
  //         maxWidth: 75,
  //         cellRenderer: (params) => (
  //           <Box
  //             height={"100%"}
  //             display={"flex"}
  //             alignItems={"center"}
  //             justifyContent={"center"}
  //           >
  //             <AgentActionMenu agent={params.data} onDelete={() => {}} />
  //           </Box>
  //         ),
  //       },
  //     ]
  //   : []),
];
