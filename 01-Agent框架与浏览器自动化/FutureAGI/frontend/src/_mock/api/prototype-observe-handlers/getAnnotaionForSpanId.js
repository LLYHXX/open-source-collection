import { http, HttpResponse } from "msw";
import { HOST_API } from "src/config-global";
import { ALL_ANNOTATORS, ALL_LABELS, ALL_LABELS_VALUES } from "./_labels";

// /tracer/annotation/<span-id>/
export const getAnnotationForSpanId = http.post(
  `${HOST_API}/tracer/annotation/:spanId`,
  async () => {
    const values = ALL_LABELS.map((label, index) => {
      return {
        ...label,
        value: ALL_LABELS_VALUES[label.id].value,
        updatedAt: new Date(),
        updatedBy: ALL_ANNOTATORS[index % ALL_ANNOTATORS.length].name,
      };
    });
    return HttpResponse.json({
      status: true,
      result: {
        annotationLabels: values,
      },
    });
  },
);
