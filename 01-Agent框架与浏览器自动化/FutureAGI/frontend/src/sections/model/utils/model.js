export function getAlertingBreakdown(monitors) {
  if (monitors?.length > 0) {
    let numTriggers = 0;
    let performance = false;
    let drift = false;
    let analytics = false;
    for (const monitor of monitors) {
      if (monitor.monitorType === "Analytics") {
        if (monitor.status) {
          numTriggers += 1;
          analytics = true;
        }
      }
      if (monitor.monitorType === "Data Drift") {
        if (monitor.status) {
          numTriggers += 1;
          drift = true;
        }
      }
      if (monitor.monitorType === "Performance") {
        if (monitor.status) {
          numTriggers += 1;
          performance = true;
        }
      }
    }
    return {
      numTriggers,
      performance,
      drift,
      analytics,
    };
  } else {
    return {
      numTriggers: null,
      performance: null,
      drift: null,
      analytics: null,
    };
  }
}
