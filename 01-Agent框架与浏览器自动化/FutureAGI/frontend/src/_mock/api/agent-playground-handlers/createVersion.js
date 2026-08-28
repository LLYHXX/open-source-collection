import { http, HttpResponse } from "msw";
import { HOST_API } from "src/config-global";

export const createVersion = http.post(
  `${HOST_API}/agent-playground/graphs/:graphId/versions/`,
  async ({ request }) => {
    const body = await request.json();

    // parseVersionResponse expects camelCase; buildVersionPayload sends snake_case
    const nodes = (body.nodes || []).map((node) => ({
      ...node,
      nodeTemplateId: node.node_template_id ?? null,
      refGraphVersionId: node.ref_graph_version_id ?? null,
      refGraphId: node.ref_graph_id ?? null,
    }));

    // parseVersionResponse expects camelCase; buildVersionPayload sends snake_case
    const edges = (body.edges || []).map((edge) => ({
      ...edge,
      sourceNodeId: edge.source_node_id ?? edge.sourceNodeId,
      targetNodeId: edge.target_node_id ?? edge.targetNodeId,
      id: edge.id || `${edge.source_node_id}-${edge.target_node_id}`,
    }));

    return HttpResponse.json({
      result: {
        id: crypto.randomUUID(),
        versionNumber: 2,
        isDraft: true,
        nodes,
        edges,
      },
    });
  },
);
