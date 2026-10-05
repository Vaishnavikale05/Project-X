import { createBrowserRouter } from "react-router-dom";

import { App } from "../pages/App";
import { AppErrorBoundary } from "./AppErrorBoundary";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    errorElement: <AppErrorBoundary />,
  },
]);
