import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function RootRedirect() {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role === 'mentor') {
    return <Navigate to="/dashboard/mentor" replace />
  }

  if (user?.role === 'mentee') {
    return <Navigate to="/dashboard/mentee" replace />
  }

  return <Navigate to="/login" replace />
}

export default RootRedirect