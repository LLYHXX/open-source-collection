import { Helmet } from "react-helmet-async";
import QueueDetailView from "src/sections/annotations/queues/view/queue-detail-view";

export default function QueueDetailPage() {
  return (
    <>
      <Helmet>
        <title>Queue Detail | Annotations</title>
      </Helmet>
      <QueueDetailView />
    </>
  );
}
