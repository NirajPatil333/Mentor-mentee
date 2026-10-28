import { useEffect, useState, useRef } from 'react'
import api from '../services/api'

function AcademicPerformance() {
  const token = localStorage.getItem('token')
  const fileInputRef = useRef(null)

  const [records, setRecords] = useState([])
  const [cgpa, setCgpa] = useState(0.0)
  const [cgpaLabel, setCgpaLabel] = useState('Calculated CGPA (Simple Average)')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [previewingId, setPreviewingId] = useState(null)
  const [downloadingId, setDownloadingId] = useState(null)

  // Form states
  const [editingId, setEditingId] = useState(null)
  const [semester, setSemester] = useState('')
  const [sgpa, setSgpa] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [existingFileName, setExistingFileName] = useState('')

  // Feedback states
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [fileError, setFileError] = useState('')

  const ALLOWED_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
  const MAX_FILE_SIZE_MB = 16

  const fetchAcademicRecords = async () => {
    try {
      setLoading(true)
      const res = await api.get('/academic-records', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setRecords(res.data.records || [])
      setCgpa(res.data.cgpa || 0.0)
      if (res.data.cgpa_label) {
        setCgpaLabel(res.data.cgpa_label)
      }
    } catch (err) {
      console.error('Failed to load academic records:', err)
      setError(err.response?.data?.message || 'Failed to load academic records.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAcademicRecords()
  }, [])

  const resetForm = () => {
    setEditingId(null)
    setSemester('')
    setSgpa('')
    setSelectedFile(null)
    setExistingFileName('')
    setFileError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    setFileError('')

    if (!file) {
      setSelectedFile(null)
      return
    }

    if (!ALLOWED_TYPES.includes(file.type)) {
      setFileError('Invalid file type. Only PDF (.pdf) and images (.png, .jpg, .jpeg) are supported.')
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setFileError(`File size exceeds ${MAX_FILE_SIZE_MB}MB limit.`)
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }

    setSelectedFile(file)
  }

  const handleEdit = (rec) => {
    setEditingId(rec.id)
    setSemester(rec.semester)
    setSgpa(rec.sgpa)
    setExistingFileName(rec.file_name || '')
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    setMessage('')
    setError('')
    setFileError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const semNum = parseInt(semester, 10)
    if (isNaN(semNum) || semNum < 1 || semNum > 16) {
      setError('Please enter a valid semester number between 1 and 16.')
      return
    }

    const sgpaNum = parseFloat(sgpa)
    if (isNaN(sgpaNum) || sgpaNum < 0 || sgpaNum > 10) {
      setError('Please enter an SGPA value between 0.00 and 10.00.')
      return
    }

    try {
      setSaving(true)
      setMessage('')
      setError('')
      setFileError('')

      const formData = new FormData()
      formData.append('semester', semNum)
      formData.append('sgpa', sgpaNum.toFixed(2))
      if (selectedFile) {
        formData.append('file', selectedFile)
      }

      const headers = {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }

      if (editingId) {
        const res = await api.put(`/academic-records/${editingId}`, formData, { headers })
        setMessage(res.data.message || 'Academic record updated successfully!')
      } else {
        const res = await api.post('/academic-records', formData, { headers })
        setMessage(res.data.message || 'Academic record added successfully!')
      }

      resetForm()
      fetchAcademicRecords()
    } catch (err) {
      console.error('Failed to save academic record:', err)
      setError(err.response?.data?.message || 'Failed to save academic record.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (recordId, semNumber) => {
    if (!window.confirm(`Are you sure you want to delete the record for Semester ${semNumber}? This will recalculate your CGPA.`)) {
      return
    }

    try {
      setDeletingId(recordId)
      const res = await api.delete(`/academic-records/${recordId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setMessage(res.data.message || 'Academic record deleted successfully.')
      fetchAcademicRecords()
    } catch (err) {
      console.error('Failed to delete academic record:', err)
      setError(err.response?.data?.message || 'Failed to delete academic record.')
    } finally {
      setDeletingId(null)
    }
  }

  const handlePreviewMarksheet = async (rec) => {
    try {
      setPreviewingId(rec.id)
      setError('')
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
      setError(err.response?.data?.message || 'Failed to preview marksheet document.')
    } finally {
      setPreviewingId(null)
    }
  }

  const handleDownloadMarksheet = async (rec) => {
    try {
      setDownloadingId(rec.id)
      setError('')
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
      setError(err.response?.data?.message || 'Failed to download marksheet document.')
    } finally {
      setDownloadingId(null)
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
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

  // Summary counts
  const totalSemesters = records.length
  const verifiedCount = records.filter(r => r.verification_status === 'verified').length
  const pendingCount = records.filter(r => r.verification_status === 'pending').length
  const rejectedCount = records.filter(r => r.verification_status === 'rejected').length

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Academic Performance</h1>
        <p className="text-slate-500 text-sm mt-1">
          Record your semester-wise SGPA, calculate your cumulative CGPA automatically, upload official marksheets, and monitor mentor verification.
        </p>
      </div>

      {/* Alerts */}
      {message && (
        <div className="p-4 bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200/80 text-sm font-medium flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage('')} className="text-emerald-600 hover:text-emerald-800 font-bold px-2 cursor-pointer">✕</button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 text-rose-700 rounded-lg border border-rose-200/80 text-sm font-medium flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-rose-500 hover:text-rose-700 font-bold px-2 cursor-pointer">✕</button>
        </div>
      )}

      {/* CGPA & Stats Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Main CGPA Card */}
        <div className="md:col-span-2 bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-2xl p-6 shadow-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider font-semibold text-blue-100">
                Cumulative Performance
              </span>
              <span className="bg-white/20 backdrop-blur-xs text-white text-[11px] px-2.5 py-0.5 rounded-full font-medium">
                Automatic Calculation
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-4xl md:text-5xl font-black tracking-tight">
                {totalSemesters > 0 ? cgpa.toFixed(2) : '--'}
              </span>
              <span className="text-lg text-blue-200 font-semibold">/ 10.00</span>
            </div>
            <p className="text-sm font-bold text-blue-100 mt-1">
              {cgpaLabel}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-white/15 text-[11px] text-blue-100/90 leading-relaxed">
            Calculated as the simple arithmetic average of all {totalSemesters} entered semester SGPAs (&Sigma; SGPA / N).
            <span className="block mt-0.5 text-blue-200/70 italic">
              Note: University-official CGPA may apply credit-weighted formulas.
            </span>
          </div>
        </div>

        {/* Total Semesters Recorded */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Entered Semesters</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <div className="mt-2">
            <p className="text-3xl font-extrabold text-slate-900">{totalSemesters}</p>
            <p className="text-xs text-slate-500 mt-1">Recorded semesters</p>
          </div>
        </div>

        {/* Verification Status Summary */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Mentor Review</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="mt-2 space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-emerald-700 font-semibold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Verified:
              </span>
              <span className="font-bold text-slate-800">{verifiedCount}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-amber-700 font-semibold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span> Pending:
              </span>
              <span className="font-bold text-slate-800">{pendingCount}</span>
            </div>
            {rejectedCount > 0 && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-rose-700 font-semibold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-500"></span> Rejected:
                </span>
                <span className="font-bold text-slate-800">{rejectedCount}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add / Edit Record Form */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              {editingId ? `Edit Performance (Semester ${semester})` : 'Add Semester Performance'}
            </h2>
            <p className="text-xs text-slate-500">
              {editingId
                ? 'Updating SGPA or replacing marksheet will reset mentor verification status to Pending.'
                : 'Enter your semester number and SGPA. You can optionally attach an official marksheet document.'}
            </p>
          </div>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 border border-slate-200 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
            >
              Cancel Edit
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Semester Number <span className="text-rose-500">*</span>
              </label>
              <select
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer"
              >
                <option value="">Select Semester</option>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Semester SGPA (0.00 – 10.00) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0.00"
                max="10.00"
                value={sgpa}
                onChange={(e) => setSgpa(e.target.value)}
                required
                placeholder="e.g. 8.45"
                className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
              />
            </div>
          </div>

          {/* Marksheet File Upload */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Official Marksheet Document <span className="text-slate-400 font-normal">(Optional for Mentor Verification)</span>
            </label>
            <div className="space-y-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400">
                Supported formats: PDF (.pdf), PNG (.png), JPG/JPEG (.jpg). Maximum size: {MAX_FILE_SIZE_MB}MB.
              </p>
              {fileError && <p className="text-xs text-rose-600 font-medium">{fileError}</p>}
              {existingFileName && !selectedFile && (
                <div className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-200/80 flex items-center gap-2">
                  <span className="font-semibold text-slate-500">Current file:</span>
                  <span className="font-mono text-slate-800">{existingFileName}</span>
                  <span className="text-[11px] text-slate-400">(Upload a new file above to replace)</span>
                </div>
              )}
            </div>
          </div>

          <div className="pt-2 flex items-center gap-3">
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-xs disabled:opacity-50 cursor-pointer text-sm"
            >
              {saving ? 'Saving...' : editingId ? 'Update Semester Record' : 'Save Semester Record'}
            </button>
            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                className="bg-white hover:bg-slate-50 text-slate-700 font-semibold px-4 py-2.5 rounded-lg border border-slate-300 transition-colors text-sm cursor-pointer"
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Semester Records List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Semester-wise Academic Records</h2>
          <span className="text-xs text-slate-500 font-medium">
            {records.length} {records.length === 1 ? 'semester' : 'semesters'} recorded
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12 text-slate-500 gap-2 bg-white rounded-xl border border-slate-200/80">
            <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="font-medium text-sm">Loading academic records...</span>
          </div>
        ) : records.length === 0 ? (
          <div className="bg-white rounded-xl p-8 border border-slate-200/80 text-center py-12">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <p className="text-base font-bold text-slate-800">No semester records added yet</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Add your semester SGPAs using the form above to track your academic progress and compute your cumulative CGPA.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-600 uppercase text-[11px] font-bold tracking-wider border-b border-slate-200/80">
                  <tr>
                    <th className="px-6 py-4">Semester</th>
                    <th className="px-6 py-4">SGPA</th>
                    <th className="px-6 py-4">Marksheet</th>
                    <th className="px-6 py-4">Mentor Verification</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {records.map((rec) => {
                    const isVerified = rec.verification_status === 'verified'
                    const isRejected = rec.verification_status === 'rejected'
                    const isPending = rec.verification_status === 'pending'

                    return (
                      <tr key={rec.id} className="hover:bg-slate-50/60 transition-colors">
                        {/* Semester */}
                        <td className="px-6 py-4 font-bold text-slate-900 whitespace-nowrap">
                          {rec.semester_name}
                        </td>

                        {/* SGPA */}
                        <td className="px-6 py-4 font-mono font-bold text-blue-600 text-base whitespace-nowrap">
                          {rec.sgpa?.toFixed(2)}
                          <span className="text-xs text-slate-400 font-normal ml-1">/ 10.0</span>
                        </td>

                        {/* Marksheet Document */}
                        <td className="px-6 py-4">
                          {rec.has_marksheet ? (
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200">
                                {rec.file_type || 'DOC'}
                              </span>
                              <button
                                onClick={() => handlePreviewMarksheet(rec)}
                                disabled={previewingId === rec.id}
                                className="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline cursor-pointer inline-flex items-center gap-1"
                                title="View document inline"
                              >
                                {previewingId === rec.id ? 'Opening...' : 'View'}
                              </button>
                              <span className="text-slate-300">|</span>
                              <button
                                onClick={() => handleDownloadMarksheet(rec)}
                                disabled={downloadingId === rec.id}
                                className="text-xs font-semibold text-slate-600 hover:text-slate-900 hover:underline cursor-pointer"
                                title="Download marksheet"
                              >
                                {downloadingId === rec.id ? 'Saving...' : 'Download'}
                              </button>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400 italic">No marksheet uploaded</span>
                          )}
                        </td>

                        {/* Verification Status */}
                        <td className="px-6 py-4">
                          <div className="space-y-1">
                            {isVerified && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                Verified
                              </span>
                            )}
                            {isPending && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200/80">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                                Pending Review
                              </span>
                            )}
                            {isRejected && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200/80">
                                <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                                Rejected
                              </span>
                            )}

                            {/* Verification Details */}
                            {rec.verified_by_name && (
                              <p className="text-[11px] text-slate-500">
                                Reviewed by <span className="font-medium text-slate-700">{rec.verified_by_name}</span>
                                {rec.verified_at && ` on ${formatDate(rec.verified_at)}`}
                              </p>
                            )}
                            {rec.review_note && (
                              <p className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-200/60 mt-1 max-w-xs italic">
                                "{rec.review_note}"
                              </p>
                            )}
                          </div>
                        </td>

                        {/* Actions */}
                        <td className="px-6 py-4 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleEdit(rec)}
                              className="text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDelete(rec.id, rec.semester)}
                              disabled={deletingId === rec.id}
                              className="text-xs font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
                            >
                              {deletingId === rec.id ? 'Deleting...' : 'Delete'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AcademicPerformance
