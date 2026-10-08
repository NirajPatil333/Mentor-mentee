import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'

import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import RootRedirect from './pages/RootRedirect'
import DashboardLayout from './components/DashboardLayout'
import MenteeDashboard from './pages/MenteeDashboard'
import MentorDashboard from './pages/MentorDashboard'
import ProtectedRoute from './components/ProtectedRoute'
import MentorProfile from './pages/MentorProfile'
import Requests from './pages/Requests'
import MenteeRequests from './pages/MenteeRequests'
import Sessions from './pages/Sessions'
import MenteeSessions from './pages/MenteeSessions'
import MenteeProfile from './pages/MenteeProfile'
import MentorProfileEdit from './pages/MentorProfileEdit'
import Resources from './pages/Resources'
import Progress from './pages/Progress'
import Certificates from './pages/Certificates'
import Achievements from './pages/Achievements'
import Feedback from './pages/Feedback'
import Ratings from './pages/Ratings'
import Mentees from './pages/Mentees'
import Availability from './pages/Availability'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>

          {/* Root redirect */}
          <Route path="/" element={<RootRedirect />} />

          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

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
            <Route path="resources" element={<Resources/>} />
            <Route path="progress" element={<Progress/>} />
            <Route path="certificates" element={<Certificates/>} />
            <Route path="achievements" element={<Achievements/>} />
            <Route path="feedback" element={<Feedback/>} />
            <Route path="ratings" element={<Ratings/>} />
            <Route path="mentees" element={<Mentees/>} />
            <Route path="availability" element={<Availability/>} />
          </Route>

        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App