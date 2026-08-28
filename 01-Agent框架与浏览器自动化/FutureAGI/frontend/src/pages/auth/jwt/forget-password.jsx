import React from "react";
import { Helmet } from "react-helmet-async";
import ForgotPasswordView from "src/sections/auth/jwt/forget-password-view";

const ForgetPassword = () => {
  return (
    <>
      <Helmet>
        <title>Forget Password</title>
      </Helmet>

      <ForgotPasswordView />
    </>
  );
};

export default ForgetPassword;
