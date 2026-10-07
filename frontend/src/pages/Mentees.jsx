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
    return <p className="text-gray-500">Loading your mentees...</p>
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Mentees</h1>
        <p className="mt-2 text-gray-600">
          View and manage all mentees with whom you have an active mentorship relationship.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {mentees.length === 0 ? (
        <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 text-center py-12">
          <p className="text-lg font-semibold text-gray-700">No active mentees yet</p>
          <p className="text-sm text-gray-500 mt-2">
            When you accept mentorship requests, your active mentees will appear here.
          </p>
          <button
            onClick={() => navigate('/dashboard/requests')}
            className="mt-6 bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 font-medium transition"
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
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition"
              >
                <div className="space-y-4">
                  {/* Card Header */}
                  <div className="flex justify-between items-start">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">{m.name || 'Mentee Candidate'}</h2>
                      <p className="text-sm text-gray-500 mt-0.5">{m.email || 'No email provided'}</p>
                    </div>
                    <span className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-xs font-bold border border-green-200">
                      Active Mentee
                    </span>
                  </div>

                  {/* Mentee Details */}
                  <div className="grid grid-cols-2 gap-3 bg-gray-50 p-3.5 rounded-lg text-xs">
                    <div>
                      <span className="font-semibold text-gray-500">Education:</span>
                      <p className="text-gray-800 font-medium mt-0.5">{m.education || 'Not specified'}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-500">Experience Level:</span>
                      <p className="text-gray-800 font-medium mt-0.5 capitalize">{m.experience_level || 'Not specified'}</p>
                    </div>
                  </div>

                  {/* Learning Goal */}
                  <div>
                    <span className="text-xs font-semibold text-gray-500">Learning Goal:</span>
                    <p className="text-sm text-gray-700 mt-1 italic bg-blue-50/50 p-3 rounded-lg border border-blue-100">
                      "{m.learning_goal || req.message || 'No specific learning goal provided.'}"
                    </p>
                  </div>

                  {/* Progress & Session Stats */}
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div className="border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500 font-medium">Scheduled Sessions</p>
                      <p className="text-lg font-bold text-gray-900 mt-1">{numSessions}</p>
                    </div>
                    <div className="border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500 font-medium">Progress Tracked</p>
                      <p className="text-lg font-bold text-gray-900 mt-1">
                        {prog ? `${avgProgress}% (${prog.count} goals)` : 'No goals yet'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-3 pt-6 border-t border-gray-100 mt-6">
                  <button
                    onClick={() => navigate('/dashboard/progress')}
                    className="flex-1 bg-blue-600 text-white font-medium text-xs py-2.5 rounded-lg hover:bg-blue-700 transition text-center"
                  >
                    View Progress
                  </button>
                  <button
                    onClick={() => navigate('/dashboard/sessions')}
                    className="flex-1 bg-gray-100 text-gray-800 font-medium text-xs py-2.5 rounded-lg hover:bg-gray-200 transition text-center"
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
