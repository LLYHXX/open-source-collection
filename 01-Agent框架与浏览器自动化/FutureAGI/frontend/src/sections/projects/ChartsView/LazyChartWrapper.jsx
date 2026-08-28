import React, { Suspense, lazy } from "react";
import PropTypes from "prop-types";
import { useInView } from "src/hooks/use-in-view";
import { Skeleton } from "@mui/material";
const ChartWithFetch = lazy(() => import("./ChartsWithFetch"));

function LazyChartWrapper({ evaluation, observeId }) {
  const [ref, inView] = useInView({ triggerOnce: false });

  return (
    <div ref={ref} style={{ minHeight: 250 }}>
      <Suspense
        fallback={<Skeleton variant="rectangular" width="100%" height={250} />}
      >
        <ChartWithFetch
          evaluation={evaluation}
          observeId={observeId}
          inView={inView}
        />
      </Suspense>
    </div>
  );
}

LazyChartWrapper.propTypes = {
  evaluation: PropTypes.object,
  handleZoomChange: PropTypes.func,
  observeId: PropTypes.string,
};

export default LazyChartWrapper;
