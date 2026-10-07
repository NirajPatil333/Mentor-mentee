import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function DashboardLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const menteeSections = [
    {
      title: null,
      links: [
        { name: 'Dashboard', path: '/dashboard/mentee' }
      ]
    },
    {
      title: 'MENTORING',
      links: [
        { name: 'Find Mentors', path: '/dashboard/mentee' },
        { name: 'Requests', path: '/dashboard/mentee-requests' },
        { name: 'Sessions', path: '/dashboard/mentee-sessions' }
      ]
    },
    {
      title: 'LEARNING',
      links: [
        { name: 'Resources', path: '/dashboard/resources' },
        { name: 'Progress', path: '/dashboard/progress' },
        { name: 'Certificates', path: '/dashboard/certificates' },
        { name: 'Achievements', path: '/dashboard/achievements' },
        { name: 'Feedback', path: '/dashboard/feedback' }
      ]
    },
    {
      title: 'PROFILE',
      links: [
        { name: 'Profile', path: '/dashboard/mentee-profile' }
      ]
    }
  ]

  const mentorSections = [
    {
      title: null,
      links: [
        { name: 'Dashboard', path: '/dashboard/mentor' }
      ]
    },
    {
      title: 'MENTORING',
      links: [
        { name: 'My Mentees', path: '/dashboard/mentees' },
        { name: 'Requests', path: '/dashboard/requests' },
        { name: 'Sessions', path: '/dashboard/sessions' }
      ]
    },
    {
      title: 'CONTENT',
      links: [
        { name: 'Resources', path: '/dashboard/resources' },
        { name: 'Progress', path: '/dashboard/progress' }
      ]
    },
    {
      title: 'PROFILE',
      links: [
        { name: 'Profile', path: '/dashboard/mentor-profile-edit' },
        { name: 'Availability', path: '/dashboard/availability' },
        { name: 'Ratings', path: '/dashboard/ratings' }
      ]
    }
  ]

  const navSections = user?.role === 'mentee' ? menteeSections : mentorSections

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r min-h-screen p-5 flex flex-col justify-between">
        <div>
          <h1 className="text-xl font-bold mb-6 text-gray-900">
            Mentor-Mentee
          </h1>

          <nav className="space-y-5">
            {navSections.map((section, idx) => (
              <div key={idx} className="space-y-1">
                {section.title && (
                  <p className="px-4 text-[10px] font-extrabold text-gray-400 uppercase tracking-wider mb-1">
                    {section.title}
                  </p>
                )}
                {section.links.map((link) => (
                  <NavLink
                    key={link.path}
                    to={link.path}
                    className={({ isActive }) =>
                      `block px-4 py-2 rounded-lg text-sm font-medium transition ${
                        isActive
                          ? 'bg-blue-600 text-white shadow-xs font-semibold'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`
                    }
                  >
                    {link.name}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
        </div>

        <button
          onClick={handleLogout}
          className="mt-8 w-full px-4 py-2 rounded-lg bg-red-500 text-white font-medium hover:bg-red-600 transition text-sm"
        >
          Logout
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-8">
        {/* Top bar */}
        <div className="bg-white rounded-lg p-4 mb-6 flex justify-between items-center border border-gray-100 shadow-xs">
          <div>
            <p className="text-xs text-gray-500 font-medium">Welcome back</p>
            <h2 className="text-lg font-bold text-gray-900">{user?.name}</h2>
          </div>

          <span className="px-3 py-1 bg-gray-100 rounded-full text-xs font-semibold text-gray-700 capitalize">
            {user?.role}
          </span>
        </div>

        <Outlet />
      </main>
    </div>
  )
}

export default DashboardLayout