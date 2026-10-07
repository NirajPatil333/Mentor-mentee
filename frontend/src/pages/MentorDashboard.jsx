import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

function MentorDashboard() {
  const navigate = useNavigate()

  const [activeMenteesCount, setActiveMenteesCount] = useState(0)
  const [pendingRequests, setPendingRequests] = useState([])
  const [upcomingSessions, setUpcomingSessions] = useState([])
  const [ratingInfo, setRatingInfo] = useState({ average_rating: 0.0, total_reviews: 0 })

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }

      const [reqRes, sessRes, rateRes] = await Promise.all([
        api.get('/requests/received', { headers }).catch(() => ({ data: { requests: [] } })),
        api.get('/sessions', { headers }).catch(() => ({ data: { sessions: [] } })),
        api.get('/feedback/mentor', { headers }).catch(() => ({ data: { average_rating: 0, total_reviews: 0 } }))
      ])

      const requests = reqRes.data.requests || []
      const sessions = sessRes.data.sessions || []

      // Active mentees count (accepted mentorship requests)
      const accepted = requests.filter(r => r.status === 'accepted')
      setActiveMenteesCount(accepted.length)

      // Pending requests list
      const pending = requests.filter(r => r.status === 'pending')
      setPendingRequests(pending)

      // Upcoming / Scheduled sessions
      const scheduled = sessions.filter(s => s.status !== 'cancelled')
      setUpcomingSessions(scheduled)

      // Rating info
      setRatingInfo({
        average_rating: rateRes.data.average_rating || 0.0,
        total_reviews: rateRes.data.total_reviews || 0
      })
    } catch (err) {
      console.error('Failed to load mentor dashboard:', err)
      setError('Unable to load some dashboard metrics. Please refresh.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <p className="text-gray-500 font-medium">Loading mentor dashboard...</p>
      </div>
    )
  }

  const avgRatingDisplay = Number(ratingInfo.average_rating).toFixed(1)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Mentor Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Overview of your active mentees, sessions, pending requests, and feedback.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {/* Overview / Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Active Mentees</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{activeMenteesCount}</p>
          </div>
          <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center text-xl font-bold">
            👥
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Pending Requests</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{pendingRequests.length}</p>
          </div>
          <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center text-xl font-bold">
            ⏳
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Upcoming Sessions</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{upcomingSessions.length}</p>
          </div>
          <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center text-xl font-bold">
            📅
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Average Rating</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{avgRatingDisplay} / 5</p>
            <p className="text-xs text-gray-400 mt-1">({ratingInfo.total_reviews} reviews)</p>
          </div>
          <div className="w-12 h-12 bg-yellow-50 text-yellow-500 rounded-xl flex items-center justify-center text-xl font-bold">
            ★
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/dashboard/availability')}
            className="p-4 bg-gray-50 hover:bg-blue-50 hover:text-blue-600 rounded-xl border border-gray-200 text-sm font-semibold text-gray-700 text-center transition"
          >
            🗓️ Manage Availability
          </button>
          <button
            onClick={() => navigate('/dashboard/requests')}
            className="p-4 bg-gray-50 hover:bg-blue-50 hover:text-blue-600 rounded-xl border border-gray-200 text-sm font-semibold text-gray-700 text-center transition"
          >
            📩 View Requests
          </button>
          <button
            onClick={() => navigate('/dashboard/sessions')}
            className="p-4 bg-gray-50 hover:bg-blue-50 hover:text-blue-600 rounded-xl border border-gray-200 text-sm font-semibold text-gray-700 text-center transition"
          >
            ➕ Schedule Session
          </button>
          <button
            onClick={() => navigate('/dashboard/ratings')}
            className="p-4 bg-gray-50 hover:bg-blue-50 hover:text-blue-600 rounded-xl border border-gray-200 text-sm font-semibold text-gray-700 text-center transition"
          >
            ⭐ View Ratings
          </button>
        </div>
      </div>

      {/* Grid: Upcoming Sessions & Pending Requests */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upcoming Sessions */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-gray-900">Upcoming Sessions</h2>
            <button
              onClick={() => navigate('/dashboard/sessions')}
              className="text-sm font-semibold text-blue-600 hover:underline"
            >
              View All
            </button>
          </div>

          {upcomingSessions.length === 0 ? (
            <div className="py-8 text-center text-gray-500">
              <p>No upcoming sessions scheduled.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {upcomingSessions.slice(0, 4).map((session) => (
                <div key={session.id} className="border border-gray-200 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-bold text-gray-900">{session.title}</h3>
                      <p className="text-sm text-gray-500">
                        Mentee: {session.mentee?.name || 'N/A'}
                      </p>
                    </div>
                    <span className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-semibold capitalize">
                      {session.status}
                    </span>
                  </div>

                  <div className="text-xs text-gray-600 flex space-x-4">
                    <span>📅 {session.scheduled_date}</span>
                    <span>⏰ {session.start_time} - {session.end_time}</span>
                  </div>

                  {session.meeting_url && (
                    <button
                      onClick={() => window.open(session.meeting_url, '_blank')}
                      className="mt-2 text-xs bg-emerald-600 text-white font-medium px-4 py-1.5 rounded-lg hover:bg-emerald-700 transition"
                    >
                      🎥 Join Meeting
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pending Requests */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-gray-900">Pending Requests</h2>
            <button
              onClick={() => navigate('/dashboard/requests')}
              className="text-sm font-semibold text-blue-600 hover:underline"
            >
              View Requests
            </button>
          </div>

          {pendingRequests.length === 0 ? (
            <div className="py-8 text-center text-gray-500">
              <p>No pending mentorship requests.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingRequests.slice(0, 4).map((req) => (
                <div key={req.id} className="border border-gray-200 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-bold text-gray-900">{req.mentee?.name || 'Mentee'}</h3>
                      <p className="text-xs text-gray-500">
                        {req.mentee?.education || req.mentee?.experience_level || 'Mentee Candidate'}
                      </p>
                    </div>
                    <span className="px-2.5 py-1 bg-amber-50 text-amber-700 rounded-full text-xs font-semibold">
                      Pending
                    </span>
                  </div>

                  {req.message && (
                    <p className="text-xs text-gray-600 bg-gray-50 p-2.5 rounded-lg italic">
                      "{req.message}"
                    </p>
                  )}

                  <div className="flex justify-end pt-1">
                    <button
                      onClick={() => navigate('/dashboard/requests')}
                      className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 transition"
                    >
                      Respond
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MentorDashboard