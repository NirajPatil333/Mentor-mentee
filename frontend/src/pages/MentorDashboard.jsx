import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { getSessionTimingState } from '../utils/sessionTiming'

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

      // Filter sessions for dashboard: only count/show future or currently ongoing sessions
      const relevantSessions = sessions.filter(s => {
        const timing = getSessionTimingState(s)
        return timing.isUpcoming || timing.isOngoing
      })
      setUpcomingSessions(relevantSessions)

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
      <div className="flex items-center justify-center min-h-[300px] text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading mentor dashboard...</span>
      </div>
    )
  }

  const avgRatingDisplay = Number(ratingInfo.average_rating).toFixed(1)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Mentor Dashboard</h1>
        <p className="mt-1.5 text-slate-500 text-sm">
          Overview of your active mentees, sessions, pending requests, and feedback.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 text-rose-700 rounded-lg border border-rose-200/80 text-sm font-medium">
          {error}
        </div>
      )}

      {/* Overview / Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex items-center justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Mentees</p>
            <p className="text-3xl font-bold text-slate-900 mt-2">{activeMenteesCount}</p>
          </div>
          <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center border border-blue-100">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex items-center justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Requests</p>
            <p className="text-3xl font-bold text-slate-900 mt-2">{pendingRequests.length}</p>
          </div>
          <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center border border-amber-100">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex items-center justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Upcoming Sessions</p>
            <p className="text-3xl font-bold text-slate-900 mt-2">{upcomingSessions.length}</p>
          </div>
          <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center border border-emerald-100">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex items-center justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Average Rating</p>
            <p className="text-3xl font-bold text-slate-900 mt-2">{avgRatingDisplay} / 5</p>
            <p className="text-xs text-slate-400 mt-1">({ratingInfo.total_reviews} reviews)</p>
          </div>
          <div className="w-12 h-12 bg-amber-50 text-amber-500 rounded-xl flex items-center justify-center border border-amber-100">
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80">
        <h2 className="text-base font-bold text-slate-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/dashboard/availability')}
            className="p-4 bg-slate-50 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 rounded-xl border border-slate-200/80 text-xs md:text-sm font-semibold text-slate-700 text-center transition-all duration-200 flex flex-col items-center gap-2 cursor-pointer"
          >
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Manage Availability</span>
          </button>

          <button
            onClick={() => navigate('/dashboard/requests')}
            className="p-4 bg-slate-50 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 rounded-xl border border-slate-200/80 text-xs md:text-sm font-semibold text-slate-700 text-center transition-all duration-200 flex flex-col items-center gap-2 cursor-pointer"
          >
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <span>View Requests</span>
          </button>

          <button
            onClick={() => navigate('/dashboard/sessions')}
            className="p-4 bg-slate-50 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 rounded-xl border border-slate-200/80 text-xs md:text-sm font-semibold text-slate-700 text-center transition-all duration-200 flex flex-col items-center gap-2 cursor-pointer"
          >
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span>Schedule Session</span>
          </button>

          <button
            onClick={() => navigate('/dashboard/ratings')}
            className="p-4 bg-slate-50 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 rounded-xl border border-slate-200/80 text-xs md:text-sm font-semibold text-slate-700 text-center transition-all duration-200 flex flex-col items-center gap-2 cursor-pointer"
          >
            <svg className="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
            <span>View Ratings</span>
          </button>
        </div>
      </div>

      {/* Grid: Upcoming Sessions & Pending Requests */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upcoming Sessions */}
        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-slate-900">Upcoming Sessions</h2>
              <button
                onClick={() => navigate('/dashboard/sessions')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 hover:underline"
              >
                View All
              </button>
            </div>

            {upcomingSessions.length === 0 ? (
              <div className="py-12 text-center text-slate-500 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                <p className="text-sm font-medium">No upcoming sessions scheduled.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {upcomingSessions.slice(0, 4).map((session) => {
                  const timing = getSessionTimingState(session)

                  return (
                    <div key={session.id} className="border border-slate-200/80 rounded-xl p-4 space-y-2 hover:border-slate-300 transition-all bg-slate-50/30">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-bold text-sm text-slate-900">{session.title}</h3>
                          <p className="text-xs text-slate-500 mt-0.5">
                            Mentee: {session.mentee?.name || 'N/A'}
                          </p>
                        </div>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize shrink-0 ${timing.badgeClass}`}>
                          {timing.displayStatus}
                        </span>
                      </div>

                      <div className="text-xs text-slate-600 flex flex-wrap gap-3 pt-1">
                        <span className="flex items-center gap-1">
                          <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span>{session.scheduled_date}</span>
                        </span>
                        <span className="flex items-center gap-1">
                          <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>{session.start_time} - {session.end_time}</span>
                        </span>
                      </div>

                      {timing.showJoinMeeting && session.meeting_url && (
                        <button
                          onClick={() => window.open(session.meeting_url, '_blank')}
                          className="mt-2 text-xs bg-emerald-600 text-white font-medium px-3.5 py-1.5 rounded-lg hover:bg-emerald-700 transition-all duration-200 flex items-center gap-1.5 cursor-pointer shadow-xs"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                          <span>Join Meeting</span>
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Pending Requests */}
        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-slate-900">Pending Requests</h2>
              <button
                onClick={() => navigate('/dashboard/requests')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 hover:underline"
              >
                View Requests
              </button>
            </div>

            {pendingRequests.length === 0 ? (
              <div className="py-12 text-center text-slate-500 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                <p className="text-sm font-medium">No pending mentorship requests.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {pendingRequests.slice(0, 4).map((req) => (
                  <div key={req.id} className="border border-slate-200/80 rounded-xl p-4 space-y-2 hover:border-slate-300 transition-all bg-slate-50/30">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-bold text-sm text-slate-900">{req.mentee?.name || 'Mentee'}</h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {req.mentee?.education || req.mentee?.experience_level || 'Mentee Candidate'}
                        </p>
                      </div>
                      <span className="px-2.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200/80 rounded-full text-xs font-semibold">
                        Pending
                      </span>
                    </div>

                    {req.message && (
                      <p className="text-xs text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200/60 italic">
                        "{req.message}"
                      </p>
                    )}

                    <div className="flex justify-end pt-1">
                      <button
                        onClick={() => navigate('/dashboard/requests')}
                        className="text-xs bg-blue-600 text-white font-medium px-3 py-1.5 rounded-lg hover:bg-blue-700 transition-all duration-200 cursor-pointer shadow-xs"
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
    </div>
  )
}

export default MentorDashboard