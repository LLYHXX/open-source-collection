// /model-hub/upload-file/
import { HOST_API } from "src/config-global";
import { http, HttpResponse } from "msw";

export const uploadFile = http.post(
  `${HOST_API}/model-hub/upload-file/`,
  async () => {
    await new Promise((resolve) => setTimeout(resolve, 500)); // Wait 3 seconds

    return HttpResponse.json({
      status: true,
      result: ["https://picsum.photos/id/237/200/300"],
    });
  },
);
