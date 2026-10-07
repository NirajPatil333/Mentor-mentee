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
import Sessions from './pages/Sessions'
import MenteeSessions from './pages/MenteeSessions'
import MenteeProfile from './pages/MenteeProfile'
import MentorProfileEdit from './pages/MentorProfileEdit'

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
            <Route path="sessions" element={<Sessions/>} />
            <Route path="mentee-sessions" element={<MenteeSessions/>}/>
            <Route path="mentee-profile" element={<MenteeProfile/>} />
            <Route path="mentor-profile-edit" element={<MentorProfileEdit/>} />
          </Route>

        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App