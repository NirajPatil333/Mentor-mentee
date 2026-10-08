import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { getSessionTimingState } from '../utils/sessionTiming'

function MenteeDashboard() {
  const [mentors, setMentors] = useState([])
  const [requestsCount, setRequestsCount] = useState(0)
  const [upcomingSessions, setUpcomingSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true)
        setError('')
        const token = localStorage.getItem('token')
        const headers = { Authorization: `Bearer ${token}` }

        const [recRes, reqRes, sessRes] = await Promise.all([
          api.get('/mentors/recommendations', { headers }).catch(() => ({ data: { recommendations: [] } })),
          api.get('/requests/sent', { headers }).catch(() => ({ data: { requests: [] } })),
          api.get('/sessions', { headers }).catch(() => ({ data: { sessions: [] } }))
        ])

        setMentors(recRes.data.recommendations || [])
        setRequestsCount((reqRes.data.requests || []).length)

        const allSessions = sessRes.data.sessions || []
        const relevantSessions = allSessions.filter(s => {
          const timing = getSessionTimingState(s)
          return timing.isUpcoming || timing.isOngoing
        })
        setUpcomingSessions(relevantSessions)
      } catch (err) {
        console.error('Failed to load mentee dashboard data:', err)
        setError(
          err.response?.data?.message ||
          'Unable to load dashboard data'
        )
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          Mentee Dashboard
        </h1>

        <p className="mt-1.5 text-slate-500 text-sm">
          Find the right mentors and manage your learning journey.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">

        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex items-center justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Recommended Mentors
            </p>

            <p className="text-3xl font-bold text-slate-900 mt-2">
              {mentors.length}
            </p>
          </div>
          <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center border border-blue-100">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex items-center justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Mentorship Requests
            </p>

            <p className="text-3xl font-bold text-slate-900 mt-2">
              {requestsCount}
            </p>
          </div>
          <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center border border-amber-100">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex items-center justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Upcoming Sessions
            </p>

            <p className="text-3xl font-bold text-slate-900 mt-2">
              {upcomingSessions.length}
            </p>
          </div>
          <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center border border-emerald-100">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>

      </div>

      {/* Upcoming Sessions Section */}
      <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80">
        <div className="flex justify-between items-center mb-6 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Upcoming Sessions
            </h2>

            <p className="text-xs text-slate-500 mt-1">
              Your scheduled mentorship sessions with video meeting links.
            </p>
          </div>

          <button
            onClick={() => navigate('/dashboard/mentee-sessions')}
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 hover:underline cursor-pointer"
          >
            View All
          </button>
        </div>

        {loading && (
          <div className="py-8 text-center flex items-center justify-center gap-2 text-slate-500">
            <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm font-medium">Loading sessions...</span>
          </div>
        )}

        {!loading && upcomingSessions.length === 0 && (
          <div className="py-8 text-center text-slate-500 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
            <p className="text-sm font-medium">No upcoming sessions scheduled.</p>
          </div>
        )}

        {!loading && upcomingSessions.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {upcomingSessions.map((session) => {
              const timing = getSessionTimingState(session)

              return (
                <div
                  key={session.id}
                  className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs hover:border-slate-300 transition-all duration-200 flex flex-col justify-between gap-3 bg-slate-50/30"
                >
                  <div className="space-y-2">
                    <div className="flex justify-between items-start gap-2">
                      <div>
                        <h3 className="font-bold text-sm text-slate-900 leading-snug">
                          {session.title}
                        </h3>
                        {session.mentor?.name && (
                          <p className="text-xs text-slate-500 mt-0.5 font-medium">
                            Mentor: {session.mentor.name}
                          </p>
                        )}
                      </div>

                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize shrink-0 ${timing.badgeClass}`}>
                        {timing.displayStatus}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-3 text-xs font-medium text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
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
                  </div>

                  {timing.showJoinMeeting && session.meeting_url && (
                    <div>
                      <button
                        onClick={() => window.open(session.meeting_url, '_blank')}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-3.5 py-1.5 rounded-lg text-xs shadow-xs transition-all duration-200 flex items-center gap-1.5 cursor-pointer"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <span>Join Meeting</span>
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Recommended Mentors Section */}
      <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80">

        <div className="mb-6 border-b border-slate-100 pb-4">
          <h2 className="text-lg font-bold text-slate-900">
            Recommended Mentors
          </h2>

          <p className="text-xs text-slate-500 mt-1">
            Mentors matched with your learning interests.
          </p>
        </div>

        {loading && (
          <div className="py-8 text-center flex items-center justify-center gap-2 text-slate-500">
            <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm font-medium">Loading mentors...</span>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200/80 text-sm text-rose-700 font-medium">
            {error}
          </div>
        )}

        {!loading && !error && mentors.length === 0 && (
          <div className="py-12 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-800">No mentor recommendations available yet</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Add your learning interests to get matched with qualified mentors.
            </p>
          </div>
        )}

        {!loading && !error && mentors.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

            {mentors.map((recommendation) => {
              const mentor = recommendation.mentor || recommendation

              return (
                <div
                  key={mentor.id || mentor.user_id}
                  className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:border-slate-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex justify-between items-start gap-2">
                      <div>
                        <h3 className="font-bold text-base text-slate-900 leading-snug">
                          {mentor.name}
                        </h3>

                        <p className="text-xs text-slate-500 mt-0.5 font-medium">
                          {mentor.current_position || 'Mentor'}
                        </p>
                      </div>

                      {recommendation.match_score !== undefined && (
                        <span className="px-2.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200/80 rounded-full text-xs font-semibold shrink-0">
                          {recommendation.match_score}% Match
                        </span>
                      )}
                    </div>

                    <div className="mt-4 space-y-2 text-xs bg-slate-50 p-3 rounded-lg border border-slate-100">
                      <div className="flex justify-between items-center text-slate-600">
                        <span className="font-medium">Experience:</span>
                        <span className="font-semibold text-slate-800">{mentor.experience_years} years</span>
                      </div>

                      <div className="flex justify-between items-center text-slate-600">
                        <span className="font-medium">Average Rating:</span>
                        <span className="font-semibold text-amber-600 flex items-center gap-1">
                          ★ {mentor.average_rating ? Number(mentor.average_rating).toFixed(1) : '5.0'} / 5
                        </span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      const completeMentor = {
                        ...(recommendation.mentor || recommendation),
                        match_score: recommendation.match_score,
                      }
                      navigate('/dashboard/mentor-profile', {
                        state: {
                          mentor: completeMentor,
                        },
                      })
                    }}
                    className="mt-5 w-full bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium py-2 rounded-lg text-xs md:text-sm transition-all duration-200 shadow-xs cursor-pointer"
                  >
                    View Profile
                  </button>
                </div>
              )
            })}

          </div>
        )}

      </div>
    </div>
  )
}

export default MenteeDashboard