import { useEffect, useState } from 'react'
import api from '../services/api'
import { getSessionTimingState } from '../utils/sessionTiming'

function MenteeSessions() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchSessions = async () => {
    try {
      const token = localStorage.getItem('token')

      const response = await api.get('/sessions', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      setSessions(response.data.sessions || [])
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Failed to load sessions.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSessions()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading sessions...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          My Sessions
        </h1>

        <p className="text-slate-500 text-sm mt-1">
          View your scheduled mentorship sessions and join video meetings.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3.5 text-sm text-rose-700 font-medium">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {sessions.length === 0 ? (
          <div className="bg-white rounded-xl p-8 border border-slate-200/80 shadow-xs text-center py-12">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-800">No sessions scheduled yet</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Your mentor will schedule upcoming sessions with you. Check back soon!
            </p>
          </div>
        ) : (
          sessions.map((session) => {
            const timing = getSessionTimingState(session)

            return (
              <div
                key={session.id}
                className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 hover:border-slate-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between gap-4"
              >
                <div className="space-y-3">
                  <div className="flex justify-between items-start gap-3">
                    <div>
                      <h2 className="text-lg font-bold text-slate-900">
                        {session.title}
                      </h2>
                      <p className="text-sm text-slate-600 mt-1">
                        {session.description || 'No description provided.'}
                      </p>
                    </div>

                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize shrink-0 ${timing.badgeClass}`}>
                      {timing.displayStatus}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-4 text-xs font-medium text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <span className="flex items-center gap-1.5">
                      <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span>Date:</span> <strong className="text-slate-900">{session.scheduled_date}</strong>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Time:</span> <strong className="text-slate-900">{session.start_time} - {session.end_time}</strong>
                    </span>
                  </div>
                </div>

                {timing.showJoinMeeting && session.meeting_url && (
                  <div className="pt-2">
                    <button
                      onClick={() =>
                        window.open(
                          session.meeting_url,
                          '_blank'
                        )
                      }
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-4 py-2 rounded-lg text-xs md:text-sm shadow-xs transition-all duration-200 flex items-center gap-1.5 cursor-pointer"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span>Join Meeting</span>
                    </button>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default MenteeSessions