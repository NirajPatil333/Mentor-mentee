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

  // Modal / Detail Panel States
  const [selectedMentee, setSelectedMentee] = useState(null)
  const [activeTab, setActiveTab] = useState('certificates') // 'certificates' | 'achievements' | 'academics'
  const [modalLoading, setModalLoading] = useState(false)
  const [modalError, setModalError] = useState('')
  const [menteeCertificates, setMenteeCertificates] = useState([])
  const [menteeAchievements, setMenteeAchievements] = useState([])
  const [menteeAcademicRecords, setMenteeAcademicRecords] = useState([])
  const [menteeCgpa, setMenteeCgpa] = useState(0.0)

  // Actions states
  const [previewingCertId, setPreviewingCertId] = useState(null)
  const [downloadingCertId, setDownloadingCertId] = useState(null)
  const [previewingMarksheetId, setPreviewingMarksheetId] = useState(null)
  const [downloadingMarksheetId, setDownloadingMarksheetId] = useState(null)
  const [verifyingRecordId, setVerifyingRecordId] = useState(null)
  const [reviewNotes, setReviewNotes] = useState({})
  const [actionError, setActionError] = useState('')
  const [actionSuccess, setActionSuccess] = useState('')

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

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && selectedMentee) {
        setSelectedMentee(null)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedMentee])

  const handleOpenDetails = async (menteeObj, defaultTab = 'certificates') => {
    setSelectedMentee(menteeObj)
    setActiveTab(defaultTab)
    setModalLoading(true)
    setModalError('')
    setActionError('')
    setActionSuccess('')
    setMenteeCertificates([])
    setMenteeAchievements([])
    setMenteeAcademicRecords([])
    setMenteeCgpa(0.0)

    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }
      const menteeId = menteeObj.id

      const [certsRes, achsRes, acadRes] = await Promise.all([
        api.get(`/certificates/mentee/${menteeId}`, { headers }).catch(() => ({ data: { certificates: [] } })),
        api.get(`/achievements/mentee/${menteeId}`, { headers }).catch(() => ({ data: { achievements: [] } })),
        api.get(`/academic-records/mentee/${menteeId}`, { headers }).catch(() => ({ data: { records: [], cgpa: 0.0 } }))
      ])

      setMenteeCertificates(certsRes.data.certificates || [])
      setMenteeAchievements(achsRes.data.achievements || [])
      setMenteeAcademicRecords(acadRes.data.records || [])
      setMenteeCgpa(acadRes.data.cgpa || 0.0)

      // Initialize review notes
      const initialNotes = {}
      ;(acadRes.data.records || []).forEach(r => {
        initialNotes[r.id] = r.review_note || ''
      })
      setReviewNotes(initialNotes)

    } catch (err) {
      console.error('Failed to load mentee portfolio records:', err)
      setModalError(err.response?.data?.message || 'Failed to load mentee records.')
    } finally {
      setModalLoading(false)
    }
  }

  const handlePreviewCertificate = async (cert) => {
    try {
      setPreviewingCertId(cert.id)
      setActionError('')
      const token = localStorage.getItem('token')
      const response = await api.get(`/certificates/${cert.id}/preview`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      })

      const contentType = response.headers['content-type'] || (cert.file_type === 'pdf' ? 'application/pdf' : 'image/jpeg')
      const blob = new Blob([response.data], { type: contentType })
      const previewUrl = window.URL.createObjectURL(blob)
      window.open(previewUrl, '_blank')
    } catch (err) {
      console.error('Failed to preview certificate:', err)
      setActionError(err.response?.data?.message || 'Failed to preview certificate.')
    } finally {
      setPreviewingCertId(null)
    }
  }

  const handleDownloadCertificate = async (cert) => {
    try {
      setDownloadingCertId(cert.id)
      setActionError('')
      const token = localStorage.getItem('token')
      const response = await api.get(`/certificates/${cert.id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      })

      const blob = new Blob([response.data], {
        type: response.headers['content-type'] || 'application/octet-stream'
      })
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl

      const fileName = cert.file_name || `${cert.title || 'certificate'}.${cert.file_type || 'pdf'}`
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      console.error('Failed to download certificate:', err)
      setActionError(err.response?.data?.message || 'Failed to download certificate.')
    } finally {
      setDownloadingCertId(null)
    }
  }

  const handlePreviewMarksheet = async (rec) => {
    try {
      setPreviewingMarksheetId(rec.id)
      setActionError('')
      const token = localStorage.getItem('token')
      const response = await api.get(`/academic-records/${rec.id}/preview`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      })

      const contentType = response.headers['content-type'] || (rec.file_type === 'pdf' ? 'application/pdf' : 'image/jpeg')
      const blob = new Blob([response.data], { type: contentType })
      const previewUrl = window.URL.createObjectURL(blob)
      window.open(previewUrl, '_blank')
    } catch (err) {
      console.error('Failed to preview marksheet:', err)
      setActionError(err.response?.data?.message || 'Failed to preview marksheet document.')
    } finally {
      setPreviewingMarksheetId(null)
    }
  }

  const handleDownloadMarksheet = async (rec) => {
    try {
      setDownloadingMarksheetId(rec.id)
      setActionError('')
      const token = localStorage.getItem('token')
      const response = await api.get(`/academic-records/${rec.id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      })

      const blob = new Blob([response.data], {
        type: response.headers['content-type'] || 'application/octet-stream'
      })
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl

      const fileName = rec.file_name || `Semester_${rec.semester}_Marksheet.${rec.file_type || 'pdf'}`
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      console.error('Failed to download marksheet:', err)
      setActionError(err.response?.data?.message || 'Failed to download marksheet document.')
    } finally {
      setDownloadingMarksheetId(null)
    }
  }

  const handleVerifyAcademicRecord = async (recordId, status) => {
    try {
      setVerifyingRecordId(recordId)
      setActionError('')
      setActionSuccess('')
      const token = localStorage.getItem('token')

      const payload = {
        status,
        review_note: reviewNotes[recordId] || ''
      }

      const res = await api.patch(`/academic-records/${recordId}/verify`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      })

      // Update local state
      const updatedRecord = res.data.record
      setMenteeAcademicRecords(prev =>
        prev.map(r => (r.id === recordId ? updatedRecord : r))
      )
      setActionSuccess(`Semester ${updatedRecord.semester} marksheet marked as ${status.toUpperCase()}!`)
    } catch (err) {
      console.error('Failed to verify record:', err)
      setActionError(err.response?.data?.message || 'Failed to update verification status.')
    } finally {
      setVerifyingRecordId(null)
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Not specified'
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading your mentees...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">My Mentees</h1>
        <p className="text-slate-500 text-sm mt-1">
          View and manage all mentees with whom you have an active mentorship relationship.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 text-rose-700 rounded-lg border border-rose-200/80 text-sm font-medium">
          {error}
        </div>
      )}

      {mentees.length === 0 ? (
        <div className="bg-white rounded-xl p-8 shadow-xs border border-slate-200/80 text-center py-12">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <p className="text-base font-bold text-slate-800">No active mentees yet</p>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            When you accept mentorship requests, your active mentees will appear here.
          </p>
          <button
            onClick={() => navigate('/dashboard/requests')}
            className="mt-6 bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-lg transition-all duration-200 shadow-xs cursor-pointer text-sm"
          >
            Review Pending Requests
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {mentees.map((req) => {
            const m = req.mentee || {}
            const menteeProfileId = m.id || req.mentee_id
            const numSessions = menteeProfileId ? (sessionCounts[menteeProfileId] || 0) : 0
            const prog = menteeProfileId ? progressSummary[menteeProfileId] : null
            const avgProgress = prog && prog.count > 0 ? Math.round(prog.totalPct / prog.count) : 0

            return (
              <div
                key={req.id}
                className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 flex flex-col justify-between hover:shadow-md hover:border-slate-300 transition-all duration-200"
              >
                <div className="space-y-4">
                  {/* Card Header */}
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <h2 className="text-lg font-bold text-slate-900">{m.name || 'Mentee Candidate'}</h2>
                      <p className="text-xs text-slate-500 mt-0.5">{m.email || 'No email provided'}</p>
                    </div>
                    <span className="px-2.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200/80 rounded-full text-xs font-semibold shrink-0">
                      Active Mentee
                    </span>
                  </div>

                  {/* Mentee Details */}
                  <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-lg text-xs border border-slate-100">
                    <div>
                      <span className="font-semibold text-slate-500">Education:</span>
                      <p className="text-slate-800 font-semibold mt-0.5">{m.education || 'Not specified'}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-slate-500">Experience Level:</span>
                      <p className="text-slate-800 font-semibold mt-0.5 capitalize">{m.experience_level || 'Not specified'}</p>
                    </div>
                  </div>

                  {/* Learning Goal */}
                  <div>
                    <span className="text-xs font-semibold text-slate-500">Learning Goal:</span>
                    <p className="text-xs text-slate-700 mt-1 italic bg-blue-50/50 p-3 rounded-lg border border-blue-100/80">
                      "{m.learning_goal || req.message || 'No specific learning goal provided.'}"
                    </p>
                  </div>

                  {/* Progress & Session Stats */}
                  <div className="grid grid-cols-2 gap-4 pt-1">
                    <div className="border border-slate-200/80 rounded-lg p-3 text-center bg-slate-50/30">
                      <p className="text-[11px] text-slate-500 font-medium uppercase tracking-wider">Scheduled Sessions</p>
                      <p className="text-base font-bold text-slate-900 mt-0.5">{numSessions}</p>
                    </div>
                    <div className="border border-slate-200/80 rounded-lg p-3 text-center bg-slate-50/30">
                      <p className="text-[11px] text-slate-500 font-medium uppercase tracking-wider">Progress Tracked</p>
                      <p className="text-base font-bold text-slate-900 mt-0.5">
                        {prog ? `${avgProgress}% (${prog.count} goals)` : 'No goals yet'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-2 pt-5 border-t border-slate-100 mt-5">
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => handleOpenDetails({ ...m, id: menteeProfileId }, 'certificates')}
                      className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs py-2 px-3 rounded-lg transition-all duration-200 shadow-xs flex items-center justify-center gap-1.5 cursor-pointer text-center"
                      title="View Certificates & Achievements"
                    >
                      <svg className="w-3.5 h-3.5 text-amber-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                      </svg>
                      <span className="truncate">Certificates</span>
                    </button>

                    <button
                      onClick={() => handleOpenDetails({ ...m, id: menteeProfileId }, 'academics')}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs py-2 px-3 rounded-lg transition-all duration-200 shadow-xs flex items-center justify-center gap-1.5 cursor-pointer text-center"
                      title="Academic Performance & Marksheets"
                    >
                      <svg className="w-3.5 h-3.5 text-indigo-200 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0112 20.055a11.952 11.952 0 01-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                      </svg>
                      <span className="truncate">Academic Records</span>
                    </button>
                  </div>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => navigate('/dashboard/progress')}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs py-2 rounded-lg transition-all duration-200 shadow-xs text-center cursor-pointer"
                    >
                      View Progress
                    </button>
                    <button
                      onClick={() => navigate('/dashboard/sessions')}
                      className="flex-1 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs py-2 rounded-lg border border-slate-300 transition-all duration-200 text-center cursor-pointer"
                    >
                      View Sessions
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Portfolio & Academic Review Modal */}
      {selectedMentee && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
          onClick={(e) => {
            if (e.target === e.currentTarget) setSelectedMentee(null)
          }}
        >
          <div className="relative bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-200 flex items-start justify-between bg-slate-50/50">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </span>
                  <h2 className="text-xl font-bold text-slate-900">
                    {selectedMentee.name || 'Mentee'}'s Portfolio & Performance
                  </h2>
                </div>
                <p className="text-xs text-slate-500 pl-8">
                  {selectedMentee.email ? `${selectedMentee.email} • ` : ''}
                  Viewing credentials, achievements, and semester marksheet records.
                </p>
              </div>
              <button
                onClick={() => setSelectedMentee(null)}
                className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-2 rounded-lg transition-colors cursor-pointer"
                title="Close modal (Esc)"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Tab Navigation */}
            <div className="px-6 border-b border-slate-200 bg-white flex space-x-6 overflow-x-auto">
              <button
                onClick={() => setActiveTab('certificates')}
                className={`py-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-2 shrink-0 ${
                  activeTab === 'certificates'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <span>Certificates</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    activeTab === 'certificates'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {menteeCertificates.length}
                </span>
              </button>

              <button
                onClick={() => setActiveTab('achievements')}
                className={`py-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-2 shrink-0 ${
                  activeTab === 'achievements'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <span>Achievements</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    activeTab === 'achievements'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {menteeAchievements.length}
                </span>
              </button>

              <button
                onClick={() => setActiveTab('academics')}
                className={`py-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-2 shrink-0 ${
                  activeTab === 'academics'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <span>Academic Performance</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    activeTab === 'academics'
                      ? 'bg-indigo-100 text-indigo-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {menteeAcademicRecords.length}
                </span>
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-4 flex-1 bg-slate-50/30">
              {actionError && (
                <div className="p-3.5 bg-rose-50 text-rose-700 rounded-lg border border-rose-200 text-xs font-medium flex items-center justify-between">
                  <span>{actionError}</span>
                  <button
                    onClick={() => setActionError('')}
                    className="text-rose-500 hover:text-rose-700 text-xs font-bold px-2 py-0.5 cursor-pointer"
                  >
                    Dismiss
                  </button>
                </div>
              )}

              {actionSuccess && (
                <div className="p-3.5 bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200 text-xs font-medium flex items-center justify-between">
                  <span>{actionSuccess}</span>
                  <button
                    onClick={() => setActionSuccess('')}
                    className="text-emerald-600 hover:text-emerald-800 text-xs font-bold px-2 py-0.5 cursor-pointer"
                  >
                    Dismiss
                  </button>
                </div>
              )}

              {modalLoading ? (
                <div className="flex flex-col items-center justify-center p-12 text-slate-500 gap-3">
                  <svg className="animate-spin h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <p className="text-sm font-medium">Loading records for {selectedMentee.name || 'mentee'}...</p>
                </div>
              ) : modalError ? (
                <div className="p-8 text-center bg-white rounded-xl border border-rose-200">
                  <div className="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <p className="text-sm font-bold text-slate-800">Failed to load records</p>
                  <p className="text-xs text-slate-500 mt-1">{modalError}</p>
                  <button
                    onClick={() => handleOpenDetails(selectedMentee, activeTab)}
                    className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                  >
                    Try Again
                  </button>
                </div>
              ) : activeTab === 'certificates' ? (
                /* Certificates Tab Content */
                menteeCertificates.length === 0 ? (
                  <div className="bg-white rounded-xl p-8 border border-slate-200/80 text-center py-12">
                    <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <p className="text-sm font-bold text-slate-800">No certificates uploaded yet</p>
                    <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                      This mentee has not uploaded any credentials or completion certificates so far.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {menteeCertificates.map((cert) => {
                      const isPdf = cert.file_type?.toLowerCase() === 'pdf'
                      const isImage = ['jpg', 'jpeg', 'png'].includes(cert.file_type?.toLowerCase())

                      return (
                        <div
                          key={cert.id}
                          className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-all"
                        >
                          <div className="space-y-3">
                            <div className="flex items-start justify-between gap-2">
                              <h3 className="text-sm font-bold text-slate-900 leading-snug line-clamp-2">
                                {cert.title}
                              </h3>
                              <span
                                className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider shrink-0 border ${
                                  isPdf
                                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                                    : isImage
                                    ? 'bg-sky-50 text-sky-700 border-sky-200'
                                    : 'bg-slate-50 text-slate-700 border-slate-200'
                                }`}
                              >
                                {cert.file_type || 'DOC'}
                              </span>
                            </div>

                            <div className="space-y-1 text-xs">
                              <div className="flex items-center gap-1.5 text-slate-600">
                                <span className="font-semibold text-slate-500">Issuer:</span>
                                <span className="font-medium text-slate-800">{cert.issuer}</span>
                              </div>
                              <div className="flex items-center gap-1.5 text-slate-600">
                                <span className="font-semibold text-slate-500">Issue Date:</span>
                                <span className="text-slate-700">{formatDate(cert.issue_date)}</span>
                              </div>
                              {cert.file_name && (
                                <div className="flex items-center gap-1.5 text-slate-500 text-[11px] truncate pt-0.5">
                                  <svg className="w-3.5 h-3.5 shrink-0 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                                  </svg>
                                  <span className="truncate" title={cert.file_name}>{cert.file_name}</span>
                                </div>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-2 pt-4 border-t border-slate-100 mt-4">
                            <button
                              onClick={() => handlePreviewCertificate(cert)}
                              disabled={previewingCertId === cert.id || downloadingCertId === cert.id}
                              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
                            >
                              {previewingCertId === cert.id ? 'Opening...' : 'View Certificate'}
                            </button>

                            <button
                              onClick={() => handleDownloadCertificate(cert)}
                              disabled={previewingCertId === cert.id || downloadingCertId === cert.id}
                              className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
                              title="Download certificate"
                            >
                              {downloadingCertId === cert.id ? '...' : 'Download'}
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )
              ) : activeTab === 'achievements' ? (
                /* Achievements Tab Content */
                menteeAchievements.length === 0 ? (
                  <div className="bg-white rounded-xl p-8 border border-slate-200/80 text-center py-12">
                    <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                      </svg>
                    </div>
                    <p className="text-sm font-bold text-slate-800">No achievements recorded yet</p>
                    <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                      This mentee has not documented any project milestones or competitive achievements so far.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {menteeAchievements.map((ach) => (
                      <div
                        key={ach.id}
                        className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs space-y-3 hover:border-slate-300 transition-all"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-0.5">
                            <h3 className="text-sm font-bold text-slate-900 leading-snug">
                              {ach.title}
                            </h3>
                            <div className="flex items-center gap-1.5 text-xs text-slate-500">
                              <span className="font-semibold text-slate-600">Date Attained:</span>
                              <span>{formatDate(ach.achievement_date)}</span>
                            </div>
                          </div>
                          <span className="text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider border bg-purple-50 text-purple-700 border-purple-200 shrink-0">
                            Achievement
                          </span>
                        </div>

                        {ach.description && (
                          <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100 leading-relaxed whitespace-pre-wrap">
                            {ach.description}
                          </p>
                        )}

                        <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                          <div>
                            {ach.achievement_url ? (
                              <a
                                href={ach.achievement_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-semibold hover:underline"
                              >
                                <span>Verification Link</span>
                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                              </a>
                            ) : (
                              <span className="text-slate-400 italic">No verification URL</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              ) : (
                /* Academic Performance & Mentor Verification Tab Content */
                <div className="space-y-5">
                  {/* CGPA Summary Banner */}
                  <div className="bg-gradient-to-r from-indigo-700 to-blue-700 text-white rounded-xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                      <span className="text-[11px] uppercase tracking-wider font-semibold text-indigo-200">
                        Calculated CGPA (Simple Average)
                      </span>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-3xl font-black">
                          {menteeAcademicRecords.length > 0 ? menteeCgpa.toFixed(2) : '--'}
                        </span>
                        <span className="text-indigo-200 text-xs font-semibold">/ 10.00</span>
                      </div>
                      <p className="text-xs text-indigo-100/80 mt-0.5">
                        Calculated across {menteeAcademicRecords.length} recorded {menteeAcademicRecords.length === 1 ? 'semester' : 'semesters'} (&Sigma; SGPA / N).
                      </p>
                    </div>

                    <div className="text-left sm:text-right text-xs text-indigo-100/80 bg-white/10 backdrop-blur-xs p-3 rounded-lg border border-white/15">
                      <p className="font-semibold text-white">Mentor Verification Policy:</p>
                      <p className="text-[11px] mt-0.5">
                        Verification confirms you reviewed the mentee's uploaded marksheet against their entered SGPA.
                      </p>
                    </div>
                  </div>

                  {menteeAcademicRecords.length === 0 ? (
                    <div className="bg-white rounded-xl p-8 border border-slate-200/80 text-center py-12">
                      <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0112 20.055a11.952 11.952 0 01-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                        </svg>
                      </div>
                      <p className="text-sm font-bold text-slate-800">No academic records recorded</p>
                      <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                        This mentee has not entered any semester SGPA or marksheet records yet.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {menteeAcademicRecords.map((rec) => {
                        const isVerified = rec.verification_status === 'verified'
                        const isRejected = rec.verification_status === 'rejected'
                        const isPending = rec.verification_status === 'pending'
                        const isReviewing = verifyingRecordId === rec.id

                        return (
                          <div
                            key={rec.id}
                            className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs space-y-4 hover:border-slate-300 transition-all"
                          >
                            {/* Card Top */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-700 font-extrabold flex items-center justify-center text-sm border border-indigo-100">
                                  S{rec.semester}
                                </div>
                                <div>
                                  <h3 className="text-sm font-bold text-slate-900">
                                    {rec.semester_name}
                                  </h3>
                                  <p className="text-xs text-slate-500">
                                    SGPA: <span className="font-bold text-blue-600 font-mono text-sm">{rec.sgpa?.toFixed(2)}</span> / 10.00
                                  </p>
                                </div>
                              </div>

                              {/* Status Badge */}
                              <div>
                                {isVerified && (
                                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                    Verified
                                  </span>
                                )}
                                {isPending && (
                                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                                    <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                                    Pending Review
                                  </span>
                                )}
                                {isRejected && (
                                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                                    <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                                    Rejected
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Marksheet Actions & Document info */}
                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                              <div>
                                <span className="font-semibold text-slate-500 block mb-0.5">Official Marksheet:</span>
                                {rec.has_marksheet ? (
                                  <div className="flex items-center gap-2">
                                    <span className="px-2 py-0.5 rounded font-bold uppercase tracking-wider text-[10px] bg-slate-200/70 text-slate-700">
                                      {rec.file_type || 'DOC'}
                                    </span>
                                    <span className="font-mono text-slate-700 max-w-xs truncate" title={rec.file_name}>
                                      {rec.file_name}
                                    </span>
                                  </div>
                                ) : (
                                  <span className="text-slate-400 italic">No document attached by mentee</span>
                                )}
                              </div>

                              {rec.has_marksheet && (
                                <div className="flex items-center gap-2 shrink-0">
                                  <button
                                    onClick={() => handlePreviewMarksheet(rec)}
                                    disabled={previewingMarksheetId === rec.id}
                                    className="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg font-semibold transition-colors disabled:opacity-50 cursor-pointer"
                                  >
                                    {previewingMarksheetId === rec.id ? 'Opening...' : 'View Marksheet'}
                                  </button>
                                  <button
                                    onClick={() => handleDownloadMarksheet(rec)}
                                    disabled={downloadingMarksheetId === rec.id}
                                    className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg font-semibold transition-colors disabled:opacity-50 cursor-pointer"
                                  >
                                    {downloadingMarksheetId === rec.id ? 'Saving...' : 'Download'}
                                  </button>
                                </div>
                              )}
                            </div>

                            {/* Verification Review Details if present */}
                            {rec.verified_by_name && (
                              <div className="text-xs text-slate-500 space-y-1">
                                <p>
                                  Last reviewed by <span className="font-semibold text-slate-700">{rec.verified_by_name}</span>
                                  {rec.verified_at && ` on ${formatDate(rec.verified_at)}`}
                                </p>
                                {rec.review_note && (
                                  <p className="bg-slate-50 p-2.5 rounded border border-slate-200/70 italic text-slate-600">
                                    Note: "{rec.review_note}"
                                  </p>
                                )}
                              </div>
                            )}

                            {/* Mentor Verification Controls */}
                            <div className="pt-2 border-t border-slate-100 space-y-2">
                              <label className="block text-xs font-semibold text-slate-700">
                                Mentor Verification Review:
                              </label>
                              <div className="flex flex-col sm:flex-row gap-2">
                                <input
                                  type="text"
                                  placeholder="Optional review note (e.g. Verified SGPA against official marksheet)..."
                                  value={reviewNotes[rec.id] !== undefined ? reviewNotes[rec.id] : ''}
                                  onChange={(e) =>
                                    setReviewNotes(prev => ({ ...prev, [rec.id]: e.target.value }))
                                  }
                                  maxLength={500}
                                  className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                                />

                                <div className="flex items-center gap-2 shrink-0">
                                  <button
                                    onClick={() => handleVerifyAcademicRecord(rec.id, 'verified')}
                                    disabled={isReviewing}
                                    className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer flex items-center gap-1"
                                  >
                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                    </svg>
                                    <span>{isReviewing ? 'Saving...' : 'Verify'}</span>
                                  </button>

                                  <button
                                    onClick={() => handleVerifyAcademicRecord(rec.id, 'rejected')}
                                    disabled={isReviewing}
                                    className="px-4 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer flex items-center gap-1"
                                  >
                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                    <span>{isReviewing ? 'Saving...' : 'Reject'}</span>
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={() => setSelectedMentee(null)}
                className="px-5 py-2 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Mentees
