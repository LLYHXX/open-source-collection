/* eslint-disable react-refresh/only-export-components */

import React from "react";
import lazyWithRetry from "src/utils/lazyWithRetry";

// ----------------------------------------------------------------------

const Page404 = lazyWithRetry(() => import("src/pages/404"));

// ----------------------------------------------------------------------

export const mainRoutes = [
  {
    // element: (
    //   <CompactLayout>
    //     <Outlet />
    //   </CompactLayout>
    // ),
    children: [{ path: "404", element: <Page404 /> }],
  },
];
