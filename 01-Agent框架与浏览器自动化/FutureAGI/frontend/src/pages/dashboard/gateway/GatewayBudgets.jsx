import React from "react";
import { Helmet } from "react-helmet-async";
import BudgetRBACSection from "src/sections/gateway/budgets/BudgetRBACSection";

const GatewayBudgets = () => (
  <>
    <Helmet>
      <title>Gateway Budgets | Future AGI</title>
    </Helmet>
    <BudgetRBACSection />
  </>
);

export default GatewayBudgets;
