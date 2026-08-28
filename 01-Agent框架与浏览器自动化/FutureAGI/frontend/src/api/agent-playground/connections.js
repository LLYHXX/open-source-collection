import axios, { endpoints } from "src/utils/axios";

/**
 * Creates a node connection (edge) via POST.
 *
 * @param {Object} payload
 * @param {string} payload.graphId - Graph ID
 * @param {string} payload.versionId - Version ID
 * @param {Object} payload.data - { id, source_node_id, target_node_id }
 * @returns {Promise<Object>} Created connection from backend
 */
export const createConnectionApi = async (payload) => {
  const res = await axios.post(
    endpoints.agentPlayground.createConnection(
      payload.graphId,
      payload.versionId,
    ),
    payload.data,
  );
  return res.data?.result;
};

/**
 * Deletes a node connection (edge) via DELETE.
 *
 * @param {Object} payload
 * @param {string} payload.graphId - Graph ID
 * @param {string} payload.versionId - Version ID
 * @param {string} payload.connectionId - NodeConnection ID
 * @returns {Promise<Object>} Deletion result
 */
export const deleteConnectionApi = async (payload) => {
  const res = await axios.delete(
    endpoints.agentPlayground.deleteConnection(
      payload.graphId,
      payload.versionId,
      payload.connectionId,
    ),
  );
  return res.data?.result;
};
