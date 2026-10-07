import { useEffect, useState } from 'react'
import api from '../services/api'

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
    return <p>Loading sessions...</p>
  }

  if (error) {
    return <p className="text-red-600">{error}</p>
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">
        My Sessions
      </h1>

      <p className="text-gray-500 mt-1">
        View your scheduled mentorship sessions and join meetings.
      </p>

      <div className="mt-6 space-y-4">
        {sessions.length === 0 ? (
          <div className="bg-white rounded-lg p-6">
            <p className="text-gray-500">
              No sessions scheduled yet.
            </p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className="bg-white rounded-lg p-6 shadow-sm"
            >
              <h2 className="text-xl font-semibold">
                {session.title}
              </h2>

              <p className="text-gray-600 mt-2">
                {session.description || 'No description provided.'}
              </p>

              <div className="mt-4 space-y-1 text-sm text-gray-600">
                <p>
                  <span className="font-medium">Date:</span>{' '}
                  {session.scheduled_date}
                </p>

                <p>
                  <span className="font-medium">Time:</span>{' '}
                  {session.start_time} - {session.end_time}
                </p>

                <p>
                  <span className="font-medium">Status:</span>{' '}
                  <span className="capitalize">
                    {session.status}
                  </span>
                </p>
              </div>

              {session.meeting_url && (
                <button
                  onClick={() =>
                    window.open(
                      session.meeting_url,
                      '_blank'
                    )
                  }
                  className="mt-5 bg-green-600 text-white px-5 py-2 rounded-lg hover:bg-green-700"
                >
                  Join Meeting
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default MenteeSessions