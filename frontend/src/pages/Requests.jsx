import { useEffect, useState } from 'react'
import api from '../services/api'
import Avatar from '../components/Avatar'

function Requests() {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  // Full Profile Modal state
  const [selectedProfile, setSelectedProfile] = useState(null)
  const [modalLoading, setModalLoading] = useState(false)
  const [modalError, setModalError] = useState('')

  const fetchRequests = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await api.get('/requests/received', {
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

  const handleAccept = async (requestId) => {
    try {
      setActionLoading(true)
      const token = localStorage.getItem('token')
      await api.patch(
        `/requests/${requestId}/accept`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      // If modal is open for this request, update modal request_status
      if (selectedProfile && selectedProfile.requestId === requestId) {
        setSelectedProfile((prev) => ({ ...prev, request_status: 'accepted' }))
      }
      await fetchRequests()
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Failed to accept request.'
      )
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async (requestId) => {
    try {
      setActionLoading(true)
      const token = localStorage.getItem('token')
      await api.patch(
        `/requests/${requestId}/reject`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      if (selectedProfile && selectedProfile.requestId === requestId) {
        setSelectedProfile((prev) => ({ ...prev, request_status: 'rejected' }))
      }
      await fetchRequests()
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Failed to reject request.'
      )
    } finally {
      setActionLoading(false)
    }
  }

  const handleViewFullProfile = async (requestItem) => {
    const mentee = requestItem.mentee
    const menteeId = mentee?.id || mentee?.user_id
    if (!menteeId) return

    setModalError('')
    setModalLoading(true)
    setSelectedProfile({
      ...mentee,
      requestId: requestItem.id,
      request_status: requestItem.status,
      request_message: requestItem.message,
      requested_at: requestItem.requested_at,
    })

    try {
      const token = localStorage.getItem('token')
      const res = await api.get(`/mentees/${menteeId}/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.data?.mentee) {
        setSelectedProfile((prev) => ({
          ...prev,
          ...res.data.mentee,
          requestId: requestItem.id,
          request_status: requestItem.status,
          request_message: requestItem.message,
          requested_at: requestItem.requested_at,
        }))
      }
    } catch (err) {
      // Fallback gracefully to requestItem data if endpoint has issue
      console.warn('Could not fetch extra profile details, using request data:', err)
    } finally {
      setModalLoading(false)
    }
  }

  // Close modal on escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && selectedProfile) {
        setSelectedProfile(null)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedProfile])

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
          Mentorship Requests
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Review mentee backgrounds, skills, and learning goals before accepting or rejecting requests.
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-800">No mentorship requests yet</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Requests from mentees who wish to connect with you will appear here.
            </p>
          </div>
        ) : (
          requests.map((request) => {
            const mentee = request.mentee || {}
            const knownSkills = mentee.skills || []
            const learningInterests = mentee.learning_interests || []

            return (
              <div
                key={request.id}
                className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 hover:border-slate-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between gap-5"
              >
                {/* Header: Avatar, Name, Email, Status */}
                <div>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                    <div className="flex items-center gap-3.5">
                      <Avatar
                        src={mentee.profile_picture}
                        name={mentee.name}
                        size="lg"
                      />
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="text-base md:text-lg font-bold text-slate-900 leading-snug">
                            {mentee.name || 'Mentee'}
                          </h2>
                          {mentee.experience_level && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                              {mentee.experience_level}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {mentee.email || ''}
                        </p>
                        {mentee.education && (
                          <p className="text-xs text-slate-600 mt-1 font-medium flex items-center gap-1">
                            <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5z" />
                            </svg>
                            <span>{mentee.education}</span>
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-start sm:self-center">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize shrink-0 ${getStatusBadge(request.status)}`}>
                        {request.status}
                      </span>
                    </div>
                  </div>

                  {/* Mentee Bio & Learning Goal */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-xs">
                    {mentee.bio && (
                      <div className="bg-slate-50/70 p-3 rounded-lg border border-slate-100">
                        <span className="font-semibold text-slate-700 block mb-1">
                          About Mentee:
                        </span>
                        <p className="text-slate-600 leading-relaxed line-clamp-3">
                          {mentee.bio}
                        </p>
                      </div>
                    )}

                    {mentee.learning_goal && (
                      <div className="bg-slate-50/70 p-3 rounded-lg border border-slate-100">
                        <span className="font-semibold text-slate-700 block mb-1">
                          Learning Goal:
                        </span>
                        <p className="text-slate-600 leading-relaxed line-clamp-3">
                          {mentee.learning_goal}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Skills Grid: Existing Known Skills vs Skills Want to Learn */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    {/* Existing Known Skills */}
                    <div className="p-3 rounded-lg bg-emerald-50/40 border border-emerald-100">
                      <p className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        Existing Skills ({knownSkills.length})
                      </p>
                      {knownSkills.length === 0 ? (
                        <p className="text-xs text-slate-400 italic">None specified</p>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {knownSkills.map((s) => (
                            <span
                              key={s.id || s.skill_id}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-100/70 text-emerald-800 text-[11px] font-semibold"
                            >
                              <span>{s.skill_name}</span>
                              {s.proficiency && (
                                <span className="text-[9px] font-medium text-emerald-700 opacity-80">
                                  ({s.proficiency})
                                </span>
                              )}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Skills Want to Learn */}
                    <div className="p-3 rounded-lg bg-indigo-50/40 border border-indigo-100">
                      <p className="text-[11px] font-bold text-indigo-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                        Skills Want to Learn ({learningInterests.length})
                      </p>
                      {learningInterests.length === 0 ? (
                        <p className="text-xs text-slate-400 italic">None specified</p>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {learningInterests.map((li) => (
                            <span
                              key={li.id || li.skill_id}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-100/70 text-indigo-800 text-[11px] font-semibold"
                            >
                              <span>{li.skill_name}</span>
                              {li.priority && (
                                <span className="text-[9px] font-medium text-indigo-700 opacity-80">
                                  ({li.priority})
                                </span>
                              )}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Request Message */}
                  <div className="mt-4 bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                    <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                      Request Message:
                    </p>
                    <p className="text-xs md:text-sm text-slate-700 italic">
                      "{request.message || 'No message provided.'}"
                    </p>
                  </div>
                </div>

                {/* Actions: View Full Profile & Accept / Reject */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => handleViewFullProfile(request)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100/80 px-3.5 py-2 rounded-lg transition border border-blue-200/60 cursor-pointer"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    <span>View Full Profile</span>
                  </button>

                  {request.status === 'pending' && (
                    <div className="flex items-center gap-2.5">
                      <button
                        type="button"
                        onClick={() => handleAccept(request.id)}
                        disabled={actionLoading}
                        className="bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-semibold px-4 py-2 rounded-lg text-xs md:text-sm transition shadow-xs cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Accept Request</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleReject(request.id)}
                        disabled={actionLoading}
                        className="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200/80 font-semibold px-3.5 py-2 rounded-lg text-xs md:text-sm transition cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        <span>Reject</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* ------------------------------------------------------------- */}
      {/* VIEW FULL PROFILE MODAL */}
      {/* ------------------------------------------------------------- */}
      {selectedProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-100 flex items-start justify-between gap-4 sticky top-0 bg-white/95 backdrop-blur-xs z-10">
              <div className="flex items-center gap-4">
                <Avatar
                  src={selectedProfile.profile_picture}
                  name={selectedProfile.name}
                  size="xl"
                  className="ring-4 ring-blue-50"
                />
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-lg md:text-xl font-bold text-slate-900">
                      {selectedProfile.name || 'Mentee Candidate'}
                    </h3>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize ${getStatusBadge(selectedProfile.request_status)}`}>
                      {selectedProfile.request_status || 'pending'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {selectedProfile.email}
                  </p>
                  {selectedProfile.experience_level && (
                    <span className="inline-block mt-1 text-[11px] font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
                      Level: {selectedProfile.experience_level}
                    </span>
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={() => setSelectedProfile(null)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition cursor-pointer"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-5">
              {modalLoading && (
                <div className="py-8 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Loading full profile details...</span>
                </div>
              )}

              {modalError && (
                <div className="p-3 bg-rose-50 text-rose-700 border border-rose-200 rounded-lg text-xs font-medium">
                  {modalError}
                </div>
              )}

              {/* Bio & Education */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Background
                </h4>
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-2">
                  <div>
                    <span className="text-xs font-semibold text-slate-700">Education:</span>
                    <p className="text-xs text-slate-600 mt-0.5">
                      {selectedProfile.education || 'No formal education details listed.'}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-slate-700">About / Introduction:</span>
                    <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
                      {selectedProfile.bio || 'No bio introduction provided.'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Learning Goal */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Career & Learning Goals
                </h4>
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                  <p className="text-xs text-slate-700 leading-relaxed font-medium">
                    {selectedProfile.learning_goal || 'No specific goals declared yet.'}
                  </p>
                </div>
              </div>

              {/* Skills Split: Existing Known vs Learning Interests */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Existing Skills */}
                <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-100 space-y-2">
                  <h4 className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span>Existing Skills ({(selectedProfile.skills || []).length})</span>
                  </h4>
                  {(selectedProfile.skills || []).length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No known skills listed.</p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {selectedProfile.skills.map((s) => (
                        <span
                          key={s.id || s.skill_id}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-100/80 text-emerald-900 text-xs font-semibold"
                        >
                          <span>{s.skill_name}</span>
                          {s.proficiency && (
                            <span className="text-[10px] text-emerald-700 font-medium opacity-80">
                              ({s.proficiency})
                            </span>
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Skills to Learn */}
                <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-100 space-y-2">
                  <h4 className="text-xs font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                    <span>Wants to Learn ({(selectedProfile.learning_interests || []).length})</span>
                  </h4>
                  {(selectedProfile.learning_interests || []).length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No learning targets listed.</p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {selectedProfile.learning_interests.map((li) => (
                        <span
                          key={li.id || li.skill_id}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-indigo-100/80 text-indigo-900 text-xs font-semibold"
                        >
                          <span>{li.skill_name}</span>
                          {li.priority && (
                            <span className="text-[10px] text-indigo-700 font-medium opacity-80">
                              ({li.priority})
                            </span>
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Request Message */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Request Message
                </h4>
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                  <p className="text-xs md:text-sm text-slate-700 italic">
                    "{selectedProfile.request_message || 'No message provided.'}"
                  </p>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-slate-100 bg-slate-50/50 flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setSelectedProfile(null)}
                className="bg-white hover:bg-slate-100 text-slate-700 font-semibold px-4 py-2 rounded-lg text-xs md:text-sm border border-slate-200 transition cursor-pointer"
              >
                Close
              </button>

              {selectedProfile.request_status === 'pending' && (
                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={() => handleAccept(selectedProfile.requestId)}
                    disabled={actionLoading}
                    className="bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-semibold px-4 py-2 rounded-lg text-xs md:text-sm transition shadow-xs cursor-pointer disabled:opacity-50"
                  >
                    Accept Request
                  </button>

                  <button
                    type="button"
                    onClick={() => handleReject(selectedProfile.requestId)}
                    disabled={actionLoading}
                    className="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200/80 font-semibold px-4 py-2 rounded-lg text-xs md:text-sm transition cursor-pointer disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Requests
