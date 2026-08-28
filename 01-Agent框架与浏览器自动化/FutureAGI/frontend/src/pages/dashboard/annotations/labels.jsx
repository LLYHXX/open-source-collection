import { Helmet } from "react-helmet-async";
import AnnotationLabelsView from "src/sections/annotations/labels/view/annotation-labels-view";

export default function AnnotationLabelsPage() {
  return (
    <>
      <Helmet>
        <title>Labels | Annotations</title>
      </Helmet>
      <AnnotationLabelsView />
    </>
  );
}
