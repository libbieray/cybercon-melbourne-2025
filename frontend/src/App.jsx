import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Toaster } from '@/components/ui/sonner';

// Layout Components
import Layout from './components/Layout';
import LoadingSpinner from './components/LoadingSpinner';

// Authentication Pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

// Speaker Pages
import SpeakerDashboard from './pages/speaker/SpeakerDashboard';
import SessionSubmission from './pages/speaker/SessionSubmission';
import SessionEdit from './pages/speaker/SessionEdit';
import SessionView from './pages/speaker/SessionView';
import SpeakerFAQ from './pages/speaker/SpeakerFAQ';

// Manager Pages
import ManagerDashboard from './pages/manager/ManagerDashboard';
import SessionReview from './pages/manager/SessionReview';
import QuestionsManagement from './pages/manager/QuestionsManagement';
import ScheduleManagement from './pages/manager/ScheduleManagement';

// Admin Pages
import AdminDashboard from './pages/admin/AdminDashboard';
import UserManagement from './pages/admin/UserManagement';
import FAQManagement from './pages/admin/FAQManagement';
import BroadcastMessages from './pages/admin/BroadcastMessages';
import SystemStats from './pages/admin/SystemStats';

import './App.css';

// Protected Route Component
const ProtectedRoute = ({ children, requiredRoles = [] }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.some(role => 
      user.roles?.some(userRole => userRole.name === role)
    );

    if (!hasRequiredRole) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return children;
};

// Main App Routes
const AppRoutes = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={
        user ? <Navigate to="/dashboard" replace /> : <LoginPage />
      } />
      <Route path="/register" element={
        user ? <Navigate to="/dashboard" replace /> : <RegisterPage />
      } />

      {/* Protected Routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        {/* Dashboard Route - Role-based redirect */}
        <Route path="dashboard" element={<DashboardRedirect />} />

        {/* Speaker Routes */}
        <Route path="speaker" element={
          <ProtectedRoute requiredRoles={['speaker']}>
            <SpeakerDashboard />
          </ProtectedRoute>
        } />
        <Route path="speaker/sessions/new" element={
          <ProtectedRoute requiredRoles={['speaker']}>
            <SessionSubmission />
          </ProtectedRoute>
        } />
        <Route path="speaker/sessions/:id/edit" element={
          <ProtectedRoute requiredRoles={['speaker']}>
            <SessionEdit />
          </ProtectedRoute>
        } />
        <Route path="speaker/sessions/:id" element={
          <ProtectedRoute requiredRoles={['speaker']}>
            <SessionView />
          </ProtectedRoute>
        } />
        <Route path="speaker/faq" element={
          <ProtectedRoute requiredRoles={['speaker']}>
            <SpeakerFAQ />
          </ProtectedRoute>
        } />

        {/* Manager Routes */}
        <Route path="manager" element={
          <ProtectedRoute requiredRoles={['manager', 'admin']}>
            <ManagerDashboard />
          </ProtectedRoute>
        } />
        <Route path="manager/sessions/:id/review" element={
          <ProtectedRoute requiredRoles={['manager', 'admin']}>
            <SessionReview />
          </ProtectedRoute>
        } />
        <Route path="manager/questions" element={
          <ProtectedRoute requiredRoles={['manager', 'admin']}>
            <QuestionsManagement />
          </ProtectedRoute>
        } />
        <Route path="manager/schedule" element={
          <ProtectedRoute requiredRoles={['manager', 'admin']}>
            <ScheduleManagement />
          </ProtectedRoute>
        } />

        {/* Admin Routes */}
        <Route path="admin" element={
          <ProtectedRoute requiredRoles={['admin']}>
            <AdminDashboard />
          </ProtectedRoute>
        } />
        <Route path="admin/users" element={
          <ProtectedRoute requiredRoles={['admin']}>
            <UserManagement />
          </ProtectedRoute>
        } />
        <Route path="admin/faq" element={
          <ProtectedRoute requiredRoles={['admin']}>
            <FAQManagement />
          </ProtectedRoute>
        } />
        <Route path="admin/messages" element={
          <ProtectedRoute requiredRoles={['admin']}>
            <BroadcastMessages />
          </ProtectedRoute>
        } />
        <Route path="admin/stats" element={
          <ProtectedRoute requiredRoles={['admin']}>
            <SystemStats />
          </ProtectedRoute>
        } />

        {/* Default redirect */}
        <Route index element={<Navigate to="/dashboard" replace />} />
      </Route>

      {/* Unauthorized page */}
      <Route path="/unauthorized" element={
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
            <p className="text-gray-600 mb-4">You don't have permission to access this page.</p>
            <button 
              onClick={() => window.history.back()}
              className="text-blue-600 hover:text-blue-800"
            >
              Go Back
            </button>
          </div>
        </div>
      } />

      {/* 404 page */}
      <Route path="*" element={
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Page Not Found</h1>
            <p className="text-gray-600 mb-4">The page you're looking for doesn't exist.</p>
            <button 
              onClick={() => window.history.back()}
              className="text-blue-600 hover:text-blue-800"
            >
              Go Back
            </button>
          </div>
        </div>
      } />
    </Routes>
  );
};

// Dashboard Redirect Component
const DashboardRedirect = () => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Redirect based on user's primary role
  if (user.roles?.some(role => role.name === 'admin')) {
    return <Navigate to="/admin" replace />;
  } else if (user.roles?.some(role => role.name === 'manager')) {
    return <Navigate to="/manager" replace />;
  } else if (user.roles?.some(role => role.name === 'speaker')) {
    return <Navigate to="/speaker" replace />;
  }

  // Default fallback
  return <Navigate to="/speaker" replace />;
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-background">
          <AppRoutes />
          <Toaster />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;

