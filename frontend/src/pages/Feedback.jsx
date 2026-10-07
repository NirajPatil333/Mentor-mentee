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
    return <p className="text-gray-500">Loading session feedback...</p>
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Session Feedback & Rating</h1>
        <p className="mt-2 text-gray-600">
          Share your feedback and rate your mentorship sessions.
        </p>
      </div>

      {/* Form Card */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Submit Feedback</h2>

        {message && (
          <div className="mb-4 p-4 bg-green-50 text-green-700 rounded-lg border border-green-200">
            {message}
          </div>
        )}

        {error && (
          <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
            {error}
          </div>
        )}

        {sessions.length === 0 ? (
          <p className="text-gray-500 py-4">
            No sessions found. You must complete a scheduled session before submitting feedback.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Session Select */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Session
              </label>
              <select
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              <div className="p-4 bg-amber-50 text-amber-800 rounded-lg border border-amber-200">
                You have already submitted feedback for this session. Choose another session to submit new feedback.
              </div>
            ) : (
              <>
                {/* Rating Selector */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rating (1 to 5 Stars)
                  </label>
                  <div className="flex items-center space-x-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setRating(star)}
                        className={`text-2xl p-2 rounded-lg transition-colors ${
                          star <= rating
                            ? 'text-amber-400 bg-amber-50 hover:bg-amber-100'
                            : 'text-gray-300 hover:text-gray-400'
                        }`}
                      >
                        ★
                      </button>
                    ))}
                    <span className="ml-3 text-sm font-semibold text-gray-700">
                      {rating} out of 5
                    </span>
                  </div>
                </div>

                {/* Comment Textarea */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Comment / Feedback (Optional)
                  </label>
                  <textarea
                    rows={4}
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="What did you learn? How was your experience with the mentor?"
                    className="w-full border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full md:w-auto bg-blue-600 text-white font-medium px-6 py-3 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Feedback'}
                </button>
              </>
            )}
          </form>
        )}
      </div>

      {/* Previously Submitted Feedback List */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Your Past Feedback</h2>

        {submittedFeedbacks.length === 0 ? (
          <p className="text-gray-500 py-4">You have not submitted any feedback yet.</p>
        ) : (
          <div className="space-y-4">
            {submittedFeedbacks.map((fb) => (
              <div key={fb.id} className="border border-gray-200 rounded-lg p-5">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900">
                      {fb.session_title || `Session #${fb.session_id}`}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Mentor: {fb.mentor_name || 'N/A'} • Date: {fb.session_date || 'N/A'}
                    </p>
                  </div>
                  <div className="flex items-center space-x-1 bg-amber-50 px-3 py-1 rounded-full text-amber-700 font-bold text-sm border border-amber-200">
                    <span>★</span>
                    <span>{fb.rating} / 5</span>
                  </div>
                </div>

                {fb.comment && (
                  <p className="mt-3 text-gray-700 bg-gray-50 p-3 rounded-lg text-sm">
                    "{fb.comment}"
                  </p>
                )}

                <p className="mt-2 text-xs text-gray-400">
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
