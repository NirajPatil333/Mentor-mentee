import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

function Mentees() {
  const navigate = useNavigate()

  const [mentees, setMentees] = useState([])
  const [sessionCounts, setSessionCounts] = useState({})
  const [progressSummary, setProgressSummary] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchMenteesData = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }

      const [reqRes, sessRes, progRes] = await Promise.all([
        api.get('/requests/received', { headers }),
        api.get('/sessions', { headers }).catch(() => ({ data: { sessions: [] } })),
        api.get('/progress', { headers }).catch(() => ({ data: { progress: [] } }))
      ])

      const requests = reqRes.data.requests || []
      const accepted = requests.filter(r => r.status === 'accepted')
      setMentees(accepted)

      // Map session counts by mentee_id
      const sessions = sessRes.data.sessions || []
      const sCounts = {}
      sessions.forEach(s => {
        if (s.mentee_id) {
          sCounts[s.mentee_id] = (sCounts[s.mentee_id] || 0) + 1
        }
      })
      setSessionCounts(sCounts)

      // Map progress summary by mentee_id
      const progressRecords = progRes.data.progress || []
      const pSummary = {}
      progressRecords.forEach(p => {
        if (p.mentee_id) {
          if (!pSummary[p.mentee_id]) {
            pSummary[p.mentee_id] = { count: 0, totalPct: 0 }
          }
          pSummary[p.mentee_id].count += 1
          pSummary[p.mentee_id].totalPct += (p.progress_percentage || 0)
        }
      })
      setProgressSummary(pSummary)

    } catch (err) {
      console.error('Failed to load mentees:', err)
      setError(err.response?.data?.message || 'Failed to load your mentees.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMenteesData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading your mentees...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">My Mentees</h1>
        <p className="text-slate-500 text-sm mt-1">
          View and manage all mentees with whom you have an active mentorship relationship.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 text-rose-700 rounded-lg border border-rose-200/80 text-sm font-medium">
          {error}
        </div>
      )}

      {mentees.length === 0 ? (
        <div className="bg-white rounded-xl p-8 shadow-xs border border-slate-200/80 text-center py-12">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <p className="text-base font-bold text-slate-800">No active mentees yet</p>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            When you accept mentorship requests, your active mentees will appear here.
          </p>
          <button
            onClick={() => navigate('/dashboard/requests')}
            className="mt-6 bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-lg transition-all duration-200 shadow-xs cursor-pointer text-sm"
          >
            Review Pending Requests
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {mentees.map((req) => {
            const m = req.mentee || {}
            const menteeProfileId = m.id
            const numSessions = menteeProfileId ? (sessionCounts[menteeProfileId] || 0) : 0
            const prog = menteeProfileId ? progressSummary[menteeProfileId] : null
            const avgProgress = prog && prog.count > 0 ? Math.round(prog.totalPct / prog.count) : 0

            return (
              <div
                key={req.id}
                className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex flex-col justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200"
              >
                <div className="space-y-4">
                  {/* Card Header */}
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <h2 className="text-lg font-bold text-slate-900">{m.name || 'Mentee Candidate'}</h2>
                      <p className="text-xs text-slate-500 mt-0.5">{m.email || 'No email provided'}</p>
                    </div>
                    <span className="px-2.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200/80 rounded-full text-xs font-semibold shrink-0">
                      Active Mentee
                    </span>
                  </div>

                  {/* Mentee Details */}
                  <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-lg text-xs border border-slate-100">
                    <div>
                      <span className="font-semibold text-slate-500">Education:</span>
                      <p className="text-slate-800 font-semibold mt-0.5">{m.education || 'Not specified'}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-slate-500">Experience Level:</span>
                      <p className="text-slate-800 font-semibold mt-0.5 capitalize">{m.experience_level || 'Not specified'}</p>
                    </div>
                  </div>

                  {/* Learning Goal */}
                  <div>
                    <span className="text-xs font-semibold text-slate-500">Learning Goal:</span>
                    <p className="text-xs text-slate-700 mt-1 italic bg-blue-50/50 p-3 rounded-lg border border-blue-100/80">
                      "{m.learning_goal || req.message || 'No specific learning goal provided.'}"
                    </p>
                  </div>

                  {/* Progress & Session Stats */}
                  <div className="grid grid-cols-2 gap-4 pt-1">
                    <div className="border border-slate-200/80 rounded-lg p-3 text-center bg-slate-50/30">
                      <p className="text-[11px] text-slate-500 font-medium uppercase tracking-wider">Scheduled Sessions</p>
                      <p className="text-base font-bold text-slate-900 mt-0.5">{numSessions}</p>
                    </div>
                    <div className="border border-slate-200/80 rounded-lg p-3 text-center bg-slate-50/30">
                      <p className="text-[11px] text-slate-500 font-medium uppercase tracking-wider">Progress Tracked</p>
                      <p className="text-base font-bold text-slate-900 mt-0.5">
                        {prog ? `${avgProgress}% (${prog.count} goals)` : 'No goals yet'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-3 pt-5 border-t border-slate-100 mt-5">
                  <button
                    onClick={() => navigate('/dashboard/progress')}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs py-2 rounded-lg transition-all duration-200 shadow-xs text-center cursor-pointer"
                  >
                    View Progress
                  </button>
                  <button
                    onClick={() => navigate('/dashboard/sessions')}
                    className="flex-1 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs py-2 rounded-lg border border-slate-300 transition-all duration-200 text-center cursor-pointer"
                  >
                    View Sessions
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default Mentees
