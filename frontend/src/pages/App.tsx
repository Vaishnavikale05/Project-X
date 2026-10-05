import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AuthenticatedShell } from "../features/auth/AuthenticatedShell";
import { useAuth } from "../features/auth/useAuth";
import { LoginPage } from "../features/auth/LoginPage";
import { RequireAuth } from "../features/auth/RequireAuth";
import {
  AdminDashboardPage,
  CameraDetailPage,
  CamerasPage,
  ClassroomDetailPage,
  ClassroomsPage,
  InstitutionPage,
  TeacherLandingPage,
} from "../features/infrastructure/pages";

function RoleHome() {
  const { user } = useAuth();
  return user?.role === "ADMIN" ? <Navigate replace to="/admin" /> : <TeacherLandingPage />;
}

function RequireAdmin({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== "ADMIN") {
    return (
      <main className="content-page">
        <h1>Access denied</h1>
        <p role="alert">Administrator access is required for this page.</p>
      </main>
    );
  }
  return children;
}

export function App() {
  return (
    <Routes>
      <Route element={<LoginPage />} path="/login" />
      <Route element={<RequireAuth />}>
        <Route element={<AuthenticatedShell />} path="/">
          <Route index element={<RoleHome />} />
          <Route
            path="admin"
            element={
              <RequireAdmin>
                <AdminDashboardPage />
              </RequireAdmin>
            }
          />
          <Route
            path="admin/institution"
            element={
              <RequireAdmin>
                <InstitutionPage />
              </RequireAdmin>
            }
          />
          <Route
            path="admin/classrooms"
            element={
              <RequireAdmin>
                <ClassroomsPage />
              </RequireAdmin>
            }
          />
          <Route
            path="admin/classrooms/:id"
            element={
              <RequireAdmin>
                <ClassroomDetailPage />
              </RequireAdmin>
            }
          />
          <Route
            path="admin/cameras"
            element={
              <RequireAdmin>
                <CamerasPage />
              </RequireAdmin>
            }
          />
          <Route
            path="admin/cameras/:id"
            element={
              <RequireAdmin>
                <CameraDetailPage />
              </RequireAdmin>
            }
          />
        </Route>
      </Route>
      <Route element={<Navigate replace to="/" />} path="*" />
    </Routes>
  );
}
