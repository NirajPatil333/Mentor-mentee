import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import api from '../services/api'

function MentorProfile() {
  const location = useLocation()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  // Safe extraction of mentor object (supports both direct mentor and recommendation wrapper)
  const stateMentor = location.state?.mentor
  const mentor = stateMentor?.mentor && stateMentor?.name === undefined
    ? { ...stateMentor.mentor, match_score: stateMentor.match_score ?? stateMentor.mentor.match_score }
    : stateMentor

  const sendRequest = async () => {
    try {
      setLoading(true)
      setMessage('')
      setError('')

      const targetUserId = mentor?.user_id || mentor?.id

      if (!targetUserId) {
        setError('Unable to send request: mentor user ID is missing.')
        return
      }

      const token = localStorage.getItem('token')

      const response = await api.post(
        '/requests',
        {
          mentor_id: targetUserId,
          message:
            'I would like to learn from you and get guidance in my learning journey.',
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      setMessage(
        response.data.message || 'Mentorship request sent successfully!'
      )
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Failed to send mentorship request.'
      )
    } finally {
      setLoading(false)
    }
  }

  if (!mentor) {
    return (
      <div className="bg-white rounded-xl p-8 shadow-xs border border-slate-200/80 text-center space-y-4 my-6">
        <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-2">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-slate-900">
          Mentor profile not found
        </h1>
        <p className="text-sm text-slate-500 max-w-sm mx-auto">
          The requested mentor profile could not be loaded. Please return to the dashboard.
        </p>

        <button
          onClick={() => navigate('/dashboard/mentee')}
          className="mt-4 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium px-5 py-2.5 rounded-lg transition text-sm shadow-xs cursor-pointer inline-flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Dashboard</span>
        </button>
      </div>
    )
  }

  const getAvailabilityBadge = (status) => {
    const s = (status || 'available').toLowerCase()
    if (s === 'available') {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200/80'
    } else if (s === 'busy') {
      return 'bg-amber-50 text-amber-700 border-amber-200/80'
    }
    return 'bg-slate-100 text-slate-600 border-slate-200'
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate('/dashboard/mentee')}
        className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700 transition-colors cursor-pointer"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        <span>Back to Dashboard</span>
      </button>

      <div className="bg-white rounded-xl p-6 md:p-8 shadow-xs border border-slate-200/80 hover:shadow-md transition-all duration-200 space-y-8">

        {/* Profile Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
              {mentor.name || 'Mentor Profile'}
            </h1>

            <p className="text-slate-500 font-medium mt-1 text-sm">
              {mentor.current_position || 'Mentor'}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {mentor.match_score !== undefined && mentor.match_score !== null && (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200/80">
                {mentor.match_score}% Match
              </span>
            )}

            <span className={`px-3 py-1 rounded-full text-xs font-semibold border capitalize ${getAvailabilityBadge(mentor.availability_status)}`}>
              Status: {mentor.availability_status || 'Available'}
            </span>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

          <div className="border border-slate-200/80 rounded-xl p-4 bg-slate-50/50">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Experience
            </p>

            <p className="text-xl font-bold text-slate-900 mt-1">
              {mentor.experience_years || 0} years
            </p>
          </div>

          <div className="border border-slate-200/80 rounded-xl p-4 bg-slate-50/50">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Average Rating
            </p>

            <p className="text-xl font-bold text-amber-600 mt-1 flex items-center gap-1">
              <span>★</span>
              <span>{mentor.average_rating ? Number(mentor.average_rating).toFixed(1) : '0.0'} / 5</span>
            </p>
          </div>

          <div className="border border-slate-200/80 rounded-xl p-4 bg-slate-50/50">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Reviews
            </p>

            <p className="text-xl font-bold text-slate-900 mt-1">
              {mentor.total_reviews || 0}
            </p>
          </div>

          <div className="border border-slate-200/80 rounded-xl p-4 bg-slate-50/50">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Availability
            </p>

            <p className="text-xl font-bold text-slate-900 mt-1 capitalize">
              {mentor.availability_status || 'Available'}
            </p>
          </div>

        </div>

        {/* About */}
        <div className="space-y-2">
          <h2 className="text-lg font-bold text-slate-900">
            About
          </h2>

          <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
            {mentor.bio || 'No bio available yet.'}
          </p>
        </div>

        {/* Education */}
        <div className="space-y-2">
          <h2 className="text-lg font-bold text-slate-900">
            Education
          </h2>

          <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
            {mentor.education || 'No education information available yet.'}
          </p>
        </div>

        {/* Action Button & Feedback */}
        <div className="pt-4 border-t border-slate-100">
          <button
            onClick={sendRequest}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold px-6 py-3 rounded-lg transition-all duration-200 shadow-xs disabled:opacity-50 cursor-pointer flex items-center gap-2 text-sm"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Sending Request...</span>
              </>
            ) : (
              <span>Send Mentorship Request</span>
            )}
          </button>

          {message && (
            <div className="mt-4 rounded-lg bg-emerald-50 border border-emerald-200/80 p-3.5 text-sm text-emerald-700 font-medium">
              {message}
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-lg bg-rose-50 border border-rose-200/80 p-3.5 text-sm text-rose-700 font-medium">
              {error}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

export default MentorProfile