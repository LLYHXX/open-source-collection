import { createContext } from "react";

// ----------------------------------------------------------------------

export const AuthContext = createContext({
  user: {},
  authenticated: false,
});
