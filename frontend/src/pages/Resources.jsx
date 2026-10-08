import { useEffect, useState, useRef } from 'react'
import api from '../services/api'

function Resources() {
  const user = JSON.parse(localStorage.getItem('user'))
  const isMentor = user?.role === 'mentor'
  const token = localStorage.getItem('token')

  const [resources, setResources] = useState([])
  const [mentees, setMentees] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [downloadingId, setDownloadingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [targetMenteeId, setTargetMenteeId] = useState('all')
  const [selectedFile, setSelectedFile] = useState(null)

  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [fileError, setFileError] = useState('')

  const fileInputRef = useRef(null)

  const ALLOWED_EXTENSIONS = ['pdf', 'ppt', 'pptx', 'doc', 'docx']
  const MAX_FILE_SIZE_MB = 16

  const fetchResources = async () => {
    try {
      const response = await api.get('/resources', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setResources(response.data.resources || [])
    } catch (err) {
      setError(
        err.response?.data?.message || 'Failed to load resources.'
      )
    } finally {
      setLoading(false)
    }
  }

  const fetchMentees = async () => {
    if (!isMentor) return
    try {
      const response = await api.get('/resources/my-mentees', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setMentees(response.data.mentees || [])
    } catch {
      // Non-blocking if no mentees endpoint or error
    }
  }

  useEffect(() => {
    fetchResources()
    if (isMentor) {
      fetchMentees()
    }
  }, [])

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    setFileError('')
    if (!file) {
      setSelectedFile(null)
      return
    }

    const extension = file.name.split('.').pop().toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setFileError(
        `Invalid file type (.${extension}). Allowed types: PDF (.pdf), Word (.doc, .docx), PowerPoint (.ppt, .pptx)`
      )
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setFileError(
        `File size exceeds ${MAX_FILE_SIZE_MB}MB limit. Please select a smaller file.`
      )
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }

    setSelectedFile(file)
  }

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!selectedFile) {
      setFileError('Please select a document to upload.')
      return
    }

    try {
      setSaving(true)
      setMessage('')
      setError('')
      setFileError('')

      const formData = new FormData()
      formData.append('title', title.trim())
      if (description.trim()) {
        formData.append('description', description.trim())
      }
      if (targetMenteeId && targetMenteeId !== 'all') {
        formData.append('mentee_id', targetMenteeId)
      }
      formData.append('file', selectedFile)

      await api.post('/resources', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      })

      setMessage('Document uploaded and shared successfully!')

      setTitle('')
      setDescription('')
      setTargetMenteeId('all')
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      fetchResources()
    } catch (err) {
      setError(
        err.response?.data?.message || 'Failed to upload resource.'
      )
    } finally {
      setSaving(false)
    }
  }

  const handleDownload = async (resource) => {
    try {
      setDownloadingId(resource.id)
      setError('')

      const response = await api.get(`/resources/${resource.id}/download`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        responseType: 'blob',
      })

      const blob = new Blob([response.data], {
        type: response.headers['content-type'] || 'application/octet-stream',
      })
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl

      const fileName = resource.file_name || `${resource.title || 'document'}`
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      setError(
        err.response?.data?.message || 'Failed to download document.'
      )
    } finally {
      setDownloadingId(null)
    }
  }

  const handleDelete = async (resourceId) => {
    if (!window.confirm('Are you sure you want to delete this resource?')) {
      return
    }

    try {
      setDeletingId(resourceId)
      await api.delete(`/resources/${resourceId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setMessage('Resource deleted successfully.')
      fetchResources()
    } catch (err) {
      setError(
        err.response?.data?.message || 'Failed to delete resource.'
      )
    } finally {
      setDeletingId(null)
    }
  }

  const getResourceTypeBadge = (type) => {
    const normalized = (type || '').toLowerCase()
    if (normalized === 'pdf') {
      return {
        label: 'PDF Document',
        bg: 'bg-rose-50 text-rose-700 border-rose-200/80',
      }
    } else if (normalized === 'word' || normalized === 'doc' || normalized === 'docx') {
      return {
        label: 'Word Document',
        bg: 'bg-blue-50 text-blue-700 border-blue-200/80',
      }
    } else if (normalized === 'powerpoint' || normalized === 'ppt' || normalized === 'pptx') {
      return {
        label: 'PowerPoint',
        bg: 'bg-amber-50 text-amber-700 border-amber-200/80',
      }
    }
    return {
      label: type || 'Document',
      bg: 'bg-slate-100 text-slate-700 border-slate-200',
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading resources...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Learning Resources</h1>
        <p className="text-slate-500 text-sm mt-1">
          {isMentor
            ? 'Upload and share educational documents (PDF, Word, PowerPoint) with your mentees.'
            : 'Access and download learning resources shared by your mentor.'}
        </p>
      </div>

      {message && (
        <div className="bg-emerald-50 border border-emerald-200/80 text-emerald-700 px-4 py-3 rounded-lg flex justify-between items-center text-sm font-medium">
          <span>{message}</span>
          <button
            onClick={() => setMessage('')}
            className="text-emerald-700 font-bold ml-4 hover:opacity-75 cursor-pointer"
          >
            ×
          </button>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200/80 text-rose-700 px-4 py-3 rounded-lg flex justify-between items-center text-sm font-medium">
          <span>{error}</span>
          <button
            onClick={() => setError('')}
            className="text-rose-700 font-bold ml-4 hover:opacity-75 cursor-pointer"
          >
            ×
          </button>
        </div>
      )}

      {isMentor && (
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 space-y-5"
        >
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-lg font-bold text-slate-900">
              Upload New Document
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Supported formats: PDF (.pdf), Word (.doc, .docx), PowerPoint (.ppt, .pptx) up to 16MB.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Document Title <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={200}
                className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
                placeholder="e.g. System Design Architecture Guide"
              />
            </div>

            {mentees.length > 0 && (
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">
                  Share With
                </label>
                <select
                  value={targetMenteeId}
                  onChange={(e) => setTargetMenteeId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer"
                >
                  <option value="all">All My Mentees (General)</option>
                  {mentees.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.email})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Description / Notes (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows="2"
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
              placeholder="Provide context or instructions for your mentees..."
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Select Document <span className="text-rose-500">*</span>
            </label>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx,.ppt,.pptx"
                onChange={handleFileChange}
                required
                className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
              />
            </div>

            {selectedFile && (
              <div className="mt-2 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-800">Selected file:</span>{' '}
                  <span className="text-blue-600 font-semibold">{selectedFile.name}</span>{' '}
                  <span className="text-slate-500">({formatFileSize(selectedFile.size)})</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                  className="text-xs text-rose-500 hover:text-rose-700 font-semibold cursor-pointer"
                >
                  Clear
                </button>
              </div>
            )}

            {fileError && (
              <p className="mt-1 text-xs text-rose-600 font-semibold">{fileError}</p>
            )}
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-xs disabled:opacity-50 cursor-pointer text-sm"
            >
              {saving ? 'Uploading Document...' : 'Upload Document'}
            </button>
          </div>
        </form>
      )}

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-900">
            {isMentor ? 'Your Uploaded Resources' : 'Available Learning Resources'}
          </h2>
          <span className="text-xs text-slate-500 font-medium">
            {resources.length} {resources.length === 1 ? 'document' : 'documents'}
          </span>
        </div>

        {resources.length === 0 ? (
          <div className="bg-white rounded-xl p-8 border border-slate-200/80 shadow-xs text-center py-12">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-800">
              No Resources Available
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {isMentor
                ? 'You have not uploaded any learning documents yet. Use the form above to share documents with your mentees.'
                : 'No documents have been shared by your mentor yet.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {resources.map((resource) => {
              const badge = getResourceTypeBadge(resource.resource_type)
              const isDownloading = downloadingId === resource.id
              const isDeleting = deletingId === resource.id

              return (
                <div
                  key={resource.id}
                  className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs hover:border-slate-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-base font-bold text-slate-900 leading-snug">
                        {resource.title}
                      </h3>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border shrink-0 ${badge.bg}`}
                      >
                        {badge.label}
                      </span>
                    </div>

                    {resource.description && (
                      <p className="text-xs text-slate-600 line-clamp-3">
                        {resource.description}
                      </p>
                    )}

                    <div className="text-xs text-slate-500 space-y-1 pt-1 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      {resource.file_name && (
                        <p className="truncate">
                          <span className="font-semibold text-slate-700">File:</span>{' '}
                          {resource.file_name}
                        </p>
                      )}

                      {!isMentor && resource.mentor && (
                        <p>
                          <span className="font-semibold text-slate-700">Shared by:</span>{' '}
                          {resource.mentor.name || 'Your Mentor'}
                        </p>
                      )}

                      {isMentor && (
                        <p>
                          <span className="font-semibold text-slate-700">Target:</span>{' '}
                          {resource.mentee
                            ? `Shared with ${resource.mentee.name}`
                            : 'Shared with all mentees'}
                        </p>
                      )}

                      {resource.created_at && (
                        <p>
                          <span className="font-semibold text-slate-700">Uploaded:</span>{' '}
                          {new Date(resource.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                    <button
                      onClick={() => handleDownload(resource)}
                      disabled={isDownloading}
                      className="inline-flex items-center gap-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium px-3.5 py-1.5 rounded-lg text-xs transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      <span>{isDownloading ? 'Downloading...' : 'Download'}</span>
                    </button>

                    {isMentor && (
                      <button
                        onClick={() => handleDelete(resource.id)}
                        disabled={isDeleting}
                        className="text-xs text-rose-600 hover:text-rose-800 font-medium px-2.5 py-1 rounded-lg hover:bg-rose-50 transition-colors disabled:opacity-50 cursor-pointer"
                      >
                        {isDeleting ? 'Deleting...' : 'Delete'}
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default Resources