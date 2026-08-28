import { useMemo, useState } from "react";

const useListSearch = (list, key = "label") => {
  const [listSearchQuery, setListSearchQuery] = useState("");

  const filteredList = useMemo(() => {
    if (!listSearchQuery.length) return list;
    return (
      list?.filter((list) =>
        list?.[key]
          ?.toLowerCase()
          ?.includes(listSearchQuery.trim().toLowerCase()),
      ) || []
    );
  }, [key, list, listSearchQuery]);

  return {
    onListSearch: setListSearchQuery,
    listSearchQuery,
    filteredList,
  };
};

export default useListSearch;
