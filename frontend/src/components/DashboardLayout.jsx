import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function DashboardLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const menteeLinks = [
    { name: 'Dashboard', path: '/dashboard/mentee' },
    { name: 'Profile', path: '/profile' },
    { name: 'Find Mentors', path: '/mentors' },
    { name: 'Requests', path: '/dashboard/mentee-requests' },
    { name: 'Sessions', path: '/sessions' },
    { name: 'Resources', path: '/resources' },
    { name: 'Progress', path: '/progress' },
    { name: 'Certificates', path: '/certificates' },
    { name: 'Achievements', path: '/achievements' },
  ]

  const mentorLinks = [
    { name: 'Dashboard', path: '/dashboard/mentor' },
    { name: 'Profile', path: '/profile' },
    { name: 'Requests', path: '/dashboard/requests' },
    { name: 'My Mentees', path: '/mentees' },
    { name: 'Sessions', path: '/sessions' },
    { name: 'Resources', path: '/resources' },
    { name: 'Availability', path: '/availability' },
    { name: 'Ratings', path: '/ratings' },
  ]

  const links = user?.role === 'mentee'
    ? menteeLinks
    : mentorLinks

  return (
    <div className="min-h-screen bg-gray-100 flex">

      {/* Sidebar */}
      <aside className="w-64 bg-white border-r min-h-screen p-5">

        <h1 className="text-xl font-bold mb-8">
          Mentor-Mentee
        </h1>

        <nav className="space-y-2">
          {links.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `block px-4 py-2 rounded-lg ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`
              }
            >
              {link.name}
            </NavLink>
          ))}
        </nav>

        <button
          onClick={handleLogout}
          className="mt-8 w-full px-4 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600"
        >
          Logout
        </button>

      </aside>

      {/* Main content */}
      <main className="flex-1 p-8">

        {/* Top bar */}
        <div className="bg-white rounded-lg p-4 mb-6 flex justify-between items-center">
          <div>
            <p className="text-sm text-gray-500">
              Welcome back
            </p>

            <h2 className="text-lg font-semibold">
              {user?.name}
            </h2>
          </div>

          <span className="px-3 py-1 bg-gray-100 rounded-full text-sm capitalize">
            {user?.role}
          </span>
        </div>

        <Outlet />

      </main>

    </div>
  )
}

export default DashboardLayout