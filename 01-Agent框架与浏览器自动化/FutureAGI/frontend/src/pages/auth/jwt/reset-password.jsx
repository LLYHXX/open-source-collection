import React from "react";
import { Helmet } from "react-helmet-async";
import ResetPasswordView from "src/sections/auth/jwt/jwt-password-reset-view";

const ResetPassword = () => {
  return (
    <>
      <Helmet>
        <title>Reset Password</title>
      </Helmet>

      <ResetPasswordView />
    </>
  );
};

export default ResetPassword;
