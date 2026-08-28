import { Helmet } from "react-helmet-async";
import AnnotationQueuesView from "src/sections/annotations/queues/view/annotation-queues-view";

export default function AnnotationQueuesPage() {
  return (
    <>
      <Helmet>
        <title>Queues | Annotations</title>
      </Helmet>
      <AnnotationQueuesView />
    </>
  );
}
