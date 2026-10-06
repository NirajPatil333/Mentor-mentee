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
    return <p>Loading requests...</p>
  }

  if (error) {
    return <p className="text-red-600">{error}</p>
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">
        My Mentorship Requests
      </h1>

      <p className="text-gray-500 mt-1">
        Track the requests you have sent to mentors.
      </p>

      <div className="mt-6 space-y-4">
        {requests.length === 0 ? (
          <div className="bg-white rounded-lg p-6">
            <p className="text-gray-500">
              You have not sent any mentorship requests yet.
            </p>
          </div>
        ) : (
          requests.map((request) => (
            <div
              key={request.id}
              className="bg-white rounded-lg p-6 shadow-sm"
            >
              <h2 className="text-lg font-semibold">
                {request.mentor?.name || 'Mentor'}
              </h2>

              <p className="text-gray-600 mt-2">
                {request.message || 'No message provided.'}
              </p>

              <div className="mt-4">
                <span className="text-sm text-gray-500">
                  Status:
                </span>

                <span
                  className={`ml-2 px-3 py-1 rounded-full text-sm capitalize ${
                    request.status === 'accepted'
                      ? 'bg-green-100 text-green-700'
                      : request.status === 'rejected'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-yellow-100 text-yellow-700'
                  }`}
                >
                  {request.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default MenteeRequests