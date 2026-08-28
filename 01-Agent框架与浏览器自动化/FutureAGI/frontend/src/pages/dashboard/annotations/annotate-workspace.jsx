import { Helmet } from "react-helmet-async";
import AnnotateWorkspaceView from "src/sections/annotations/queues/annotate/annotate-workspace-view";

export default function AnnotateWorkspacePage() {
  return (
    <>
      <Helmet>
        <title>Annotate | FutureAGI</title>
      </Helmet>
      <AnnotateWorkspaceView />
    </>
  );
}
