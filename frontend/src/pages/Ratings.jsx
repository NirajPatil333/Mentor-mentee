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
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading ratings...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3.5 text-sm text-rose-700 font-medium">
        {error}
      </div>
    )
  }

  const avgRating = Number(data.average_rating).toFixed(1)

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Feedback & Ratings</h1>
        <p className="mt-1 text-slate-500 text-sm">
          Review ratings and feedback submitted by your mentees.
        </p>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex items-center justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Average Rating</p>
            <p className="text-3xl font-bold text-slate-900 mt-2">{avgRating} / 5.0</p>
          </div>
          <div className="w-12 h-12 bg-amber-50 rounded-xl flex items-center justify-center text-amber-500 text-xl font-bold border border-amber-200/80">
            ★
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex items-center justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Reviews</p>
            <p className="text-3xl font-bold text-slate-900 mt-2">{data.total_reviews}</p>
          </div>
          <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600 border border-blue-200/80">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Reviews List */}
      <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 space-y-4">
        <h2 className="text-lg font-bold text-slate-900 border-b border-slate-100 pb-3">Received Reviews</h2>

        {data.feedbacks.length === 0 ? (
          <div className="text-center py-12 text-slate-500 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
            <p className="text-sm font-medium">No feedback or reviews received yet.</p>
            <p className="text-xs text-slate-400 mt-1">
              Feedback from completed sessions will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {data.feedbacks.map((fb) => (
              <div key={fb.id} className="border border-slate-200/80 rounded-xl p-5 hover:border-slate-300 transition-all bg-slate-50/30 space-y-3">
                <div className="flex justify-between items-start gap-3">
                  <div>
                    <h3 className="font-bold text-base text-slate-900">
                      {fb.mentee_name || 'Anonymous Mentee'}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Session: {fb.session_title || `Session #${fb.session_id}`}
                      {fb.session_date ? ` (${fb.session_date})` : ''}
                    </p>
                  </div>
                  <div className="flex items-center space-x-1 bg-amber-50 text-amber-700 px-2.5 py-0.5 rounded-full font-bold text-xs border border-amber-200/80 shrink-0">
                    <span>★</span>
                    <span>{fb.rating} / 5</span>
                  </div>
                </div>

                {fb.comment ? (
                  <p className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-slate-100 italic">
                    "{fb.comment}"
                  </p>
                ) : (
                  <p className="text-xs text-slate-400 italic">No written comment provided.</p>
                )}

                <p className="text-[11px] text-slate-400">
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
