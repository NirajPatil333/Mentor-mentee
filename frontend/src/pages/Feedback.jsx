import { useEffect, useState } from 'react'
import api from '../services/api'

function Feedback() {
  const [sessions, setSessions] = useState([])
  const [submittedFeedbacks, setSubmittedFeedbacks] = useState([])
  const [selectedSessionId, setSelectedSessionId] = useState('')
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState('')

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const fetchData = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('token')

      const [sessRes, fbRes] = await Promise.all([
        api.get('/sessions', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/feedback/mentee', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ])

      const sessList = sessRes.data.sessions || []
      const fbList = fbRes.data.feedbacks || []

      setSessions(sessList)
      setSubmittedFeedbacks(fbList)

      const submittedSessionIds = new Set(fbList.map(f => f.session_id))
      const available = sessList.find(s => !submittedSessionIds.has(s.id))
      if (available) {
        setSelectedSessionId(available.id)
      } else if (sessList.length > 0) {
        setSelectedSessionId(sessList[0].id)
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load feedback data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage('')
    setError('')

    if (!selectedSessionId) {
      setError('Please select a session to rate.')
      return
    }

    try {
      setSubmitting(true)
      const token = localStorage.getItem('token')

      const response = await api.post(
        '/feedback',
        {
          session_id: Number(selectedSessionId),
          rating: Number(rating),
          comment: comment.trim() || undefined
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      setMessage(response.data.message || 'Feedback submitted successfully!')
      setComment('')
      await fetchData()
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to submit feedback.')
    } finally {
      setSubmitting(false)
    }
  }

  const submittedSessionIds = new Set(submittedFeedbacks.map(f => f.session_id))
  const isAlreadySubmitted = submittedSessionIds.has(Number(selectedSessionId))

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading session feedback...</span>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Session Feedback & Rating</h1>
        <p className="mt-1 text-slate-500 text-sm">
          Share your feedback and rate your completed mentorship sessions.
        </p>
      </div>

      {/* Form Card */}
      <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 space-y-6">
        <h2 className="text-lg font-bold text-slate-900 border-b border-slate-100 pb-3">Submit Feedback</h2>

        {message && (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200/80 p-3.5 text-sm text-emerald-700 font-medium">
            {message}
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3.5 text-sm text-rose-700 font-medium">
            {error}
          </div>
        )}

        {sessions.length === 0 ? (
          <div className="text-center py-8 text-slate-500 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
            <p className="text-sm font-medium">No sessions found.</p>
            <p className="text-xs text-slate-400 mt-1">You must have a scheduled session before submitting feedback.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                Select Session
              </label>
              <select
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 p-3 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer"
              >
                {sessions.map((sess) => {
                  const hasFb = submittedSessionIds.has(sess.id)
                  return (
                    <option key={sess.id} value={sess.id}>
                      {sess.title} ({sess.scheduled_date}) {hasFb ? '✓ Feedback Submitted' : ''}
                    </option>
                  )
                })}
              </select>
            </div>

            {isAlreadySubmitted ? (
              <div className="p-4 bg-amber-50 text-amber-800 rounded-lg border border-amber-200/80 text-sm font-medium">
                You have already submitted feedback for this session. Choose another session to submit new feedback.
              </div>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                    Rating (1 to 5 Stars)
                  </label>
                  <div className="flex items-center space-x-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setRating(star)}
                        className={`text-2xl p-2 rounded-lg transition-colors cursor-pointer ${
                          star <= rating
                            ? 'text-amber-500 bg-amber-50 hover:bg-amber-100'
                            : 'text-slate-300 hover:text-slate-400'
                        }`}
                      >
                        ★
                      </button>
                    ))}
                    <span className="ml-3 text-sm font-bold text-slate-700">
                      {rating} out of 5
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                    Comment / Feedback (Optional)
                  </label>
                  <textarea
                    rows={4}
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="What did you learn? How was your experience with the mentor?"
                    className="w-full rounded-lg border border-slate-300 p-3 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-xs disabled:opacity-50 cursor-pointer text-sm"
                >
                  {submitting ? 'Submitting...' : 'Submit Feedback'}
                </button>
              </>
            )}
          </form>
        )}
      </div>

      {/* Previously Submitted Feedback List */}
      <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 space-y-4">
        <h2 className="text-lg font-bold text-slate-900 border-b border-slate-100 pb-3">Your Past Feedback</h2>

        {submittedFeedbacks.length === 0 ? (
          <p className="text-xs text-slate-500 py-4 text-center">You have not submitted any feedback yet.</p>
        ) : (
          <div className="space-y-4">
            {submittedFeedbacks.map((fb) => (
              <div key={fb.id} className="border border-slate-200/80 rounded-xl p-5 hover:border-slate-300 transition-all bg-slate-50/30 space-y-3">
                <div className="flex justify-between items-start gap-3">
                  <div>
                    <h3 className="font-bold text-base text-slate-900">
                      {fb.session_title || `Session #${fb.session_id}`}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Mentor: {fb.mentor_name || 'N/A'} • Date: {fb.session_date || 'N/A'}
                    </p>
                  </div>
                  <div className="flex items-center space-x-1 bg-amber-50 text-amber-700 px-2.5 py-0.5 rounded-full font-bold text-xs border border-amber-200/80 shrink-0">
                    <span>★</span>
                    <span>{fb.rating} / 5</span>
                  </div>
                </div>

                {fb.comment && (
                  <p className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-slate-100 italic">
                    "{fb.comment}"
                  </p>
                )}

                <p className="text-[11px] text-slate-400">
                  Submitted on: {fb.created_at ? new Date(fb.created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Feedback
