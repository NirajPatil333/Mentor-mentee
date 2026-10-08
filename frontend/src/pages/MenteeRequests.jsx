import { useEffect, useState } from 'react'
import api from '../services/api'

function MenteeRequests() {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchRequests = async () => {
    try {
      const token = localStorage.getItem('token')

      const response = await api.get('/requests/sent', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      setRequests(response.data.requests || [])
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Failed to load requests.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading requests...</span>
      </div>
    )
  }

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase()
    if (s === 'accepted') {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200/80'
    } else if (s === 'rejected') {
      return 'bg-rose-50 text-rose-700 border-rose-200/80'
    }
    return 'bg-amber-50 text-amber-700 border-amber-200/80'
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          My Mentorship Requests
        </h1>

        <p className="text-slate-500 text-sm mt-1">
          Track the status of mentorship requests you have sent.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3.5 text-sm text-rose-700 font-medium">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {requests.length === 0 ? (
          <div className="bg-white rounded-xl p-8 border border-slate-200/80 shadow-xs text-center py-12">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-800">No mentorship requests sent yet</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Find mentors on your dashboard and request mentorship to get started.
            </p>
          </div>
        ) : (
          requests.map((request) => (
            <div
              key={request.id}
              className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 hover:border-slate-300 hover:shadow-md transition-all duration-200"
            >
              <div className="flex justify-between items-start gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    {request.mentor?.name || 'Mentor'}
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {request.mentor?.current_position || 'Mentor'}
                  </p>
                </div>

                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize shrink-0 ${getStatusBadge(request.status)}`}>
                  {request.status}
                </span>
              </div>

              <div className="mt-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
                <p className="text-xs font-semibold text-slate-500 mb-1">Your Message:</p>
                <p className="text-sm text-slate-700 italic">
                  "{request.message || 'No message provided.'}"
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default MenteeRequests