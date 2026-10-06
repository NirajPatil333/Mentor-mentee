import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'

import Login from './pages/Login'
import Register from './pages/Register'
import DashboardLayout from './components/DashboardLayout'
import MenteeDashboard from './pages/MenteeDashboard'
import MentorDashboard from './pages/MentorDashboard'
import ProtectedRoute from './components/ProtectedRoute'
import MentorProfile from './pages/mentorProfile'
import Requests from './pages/Requests'
import MenteeRequests from './pages/MenteeRequests'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>

          {/* Public routes */}
          <Route path="/" element={<Login />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected dashboard */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route path="mentee" element={<MenteeDashboard />} />
            <Route path="mentor" element={<MentorDashboard />} />
            <Route path="mentor-profile" element={<MentorProfile />} />
            <Route path="requests" element={<Requests/>} />
            <Route path="mentee-requests" element={<MenteeRequests/>} />
          </Route>

        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App