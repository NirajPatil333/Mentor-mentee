import { useEffect, useState } from 'react'
import api from '../services/api'

function Ratings() {
  const [data, setData] = useState({
    average_rating: 0.0,
    total_reviews: 0,
    feedbacks: []
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchRatings = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await api.get('/feedback/mentor', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setData({
        average_rating: response.data.average_rating || 0.0,
        total_reviews: response.data.total_reviews || 0,
        feedbacks: response.data.feedbacks || []
      })
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load ratings.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRatings()
  }, [])

  if (loading) {
    return <p className="text-gray-500">Loading feedback & ratings...</p>
  }

  if (error) {
    return <p className="text-red-600">{error}</p>
  }

  const avgRating = Number(data.average_rating).toFixed(1)

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Feedback & Ratings</h1>
        <p className="mt-2 text-gray-600">
          Review ratings and feedback submitted by your mentees.
        </p>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Average Rating</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{avgRating} / 5.0</p>
          </div>
          <div className="w-14 h-14 bg-amber-50 rounded-full flex items-center justify-center text-amber-500 text-2xl font-bold border border-amber-200">
            ★
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Total Reviews</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{data.total_reviews}</p>
          </div>
          <div className="w-14 h-14 bg-blue-50 rounded-full flex items-center justify-center text-blue-600 text-2xl font-bold border border-blue-200">
            💬
          </div>
        </div>
      </div>

      {/* Reviews List */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Received Reviews</h2>

        {data.feedbacks.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No feedback or reviews received yet.</p>
            <p className="text-sm text-gray-400 mt-1">
              Feedback from completed sessions will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {data.feedbacks.map((fb) => (
              <div key={fb.id} className="border border-gray-200 rounded-lg p-5 hover:border-gray-300 transition">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900">
                      {fb.mentee_name || 'Anonymous Mentee'}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Session: {fb.session_title || `Session #${fb.session_id}`}
                      {fb.session_date ? ` (${fb.session_date})` : ''}
                    </p>
                  </div>
                  <div className="flex items-center space-x-1 bg-amber-50 px-3 py-1 rounded-full text-amber-700 font-bold text-sm border border-amber-200">
                    <span>★</span>
                    <span>{fb.rating} / 5</span>
                  </div>
                </div>

                {fb.comment ? (
                  <p className="mt-3 text-gray-700 bg-gray-50 p-3 rounded-lg text-sm italic">
                    "{fb.comment}"
                  </p>
                ) : (
                  <p className="mt-2 text-sm text-gray-400 italic">No written comment provided.</p>
                )}

                <p className="mt-3 text-xs text-gray-400">
                  Received on: {fb.created_at ? new Date(fb.created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Ratings
