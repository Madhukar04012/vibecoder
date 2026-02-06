import { createBrowserRouter } from "react-router-dom"
import App from "@/App"
import Login from "@/pages/auth/Login"
import Signup from "@/pages/auth/Signup"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/signup",
    element: <Signup />,
  },
])
