import { Helmet } from "react-helmet-async";
import IntegrationsList from "src/sections/settings/integrations/IntegrationsList";

export default function IntegrationsPage() {
  return (
    <>
      <Helmet>
        <title>Integrations | FutureAGI</title>
      </Helmet>
      <IntegrationsList />
    </>
  );
}
