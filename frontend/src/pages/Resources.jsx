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

      // Get filename from resource or header
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
        bg: 'bg-red-100 text-red-800 border-red-200',
        icon: '📄',
      }
    } else if (normalized === 'word' || normalized === 'doc' || normalized === 'docx') {
      return {
        label: 'Word Document',
        bg: 'bg-blue-100 text-blue-800 border-blue-200',
        icon: '📝',
      }
    } else if (normalized === 'powerpoint' || normalized === 'ppt' || normalized === 'pptx') {
      return {
        label: 'PowerPoint',
        bg: 'bg-orange-100 text-orange-800 border-orange-200',
        icon: '📊',
      }
    }
    return {
      label: type || 'Document',
      bg: 'bg-gray-100 text-gray-800 border-gray-200',
      icon: '📁',
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-gray-500 font-medium">Loading resources...</p>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Learning Resources</h1>
        <p className="text-gray-600 mt-1">
          {isMentor
            ? 'Upload and share learning documents (PDF, Word, PowerPoint) with your mentees.'
            : 'Access and download educational documents shared by your mentor.'}
        </p>
      </div>

      {message && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex justify-between items-center">
          <span>{message}</span>
          <button
            onClick={() => setMessage('')}
            className="text-green-700 font-bold ml-4 hover:opacity-75"
          >
            ×
          </button>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button
            onClick={() => setError('')}
            className="text-red-700 font-bold ml-4 hover:opacity-75"
          >
            ×
          </button>
        </div>
      )}

      {isMentor && (
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 space-y-5"
        >
          <div className="border-b border-gray-100 pb-3">
            <h2 className="text-lg font-bold text-gray-900">
              Upload New Document
            </h2>
            <p className="text-sm text-gray-500">
              Supported formats: PDF (.pdf), Word (.doc, .docx), PowerPoint (.ppt, .pptx) up to 16MB.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Document Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={200}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="e.g. System Design Cheat Sheet"
              />
            </div>

            {mentees.length > 0 && (
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Share With
                </label>
                <select
                  value={targetMenteeId}
                  onChange={(e) => setTargetMenteeId(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
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
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Description / Notes (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows="2"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="Provide context or instructions for your mentees..."
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Select Document <span className="text-red-500">*</span>
            </label>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx,.ppt,.pptx"
                onChange={handleFileChange}
                required
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
              />
            </div>

            {selectedFile && (
              <div className="mt-2 text-sm text-gray-600 bg-gray-50 p-2.5 rounded-lg border border-gray-200 flex items-center justify-between">
                <div>
                  <span className="font-medium text-gray-800">Selected file:</span>{' '}
                  <span className="text-blue-600 font-semibold">{selectedFile.name}</span>{' '}
                  <span className="text-gray-500">({formatFileSize(selectedFile.size)})</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                  className="text-xs text-red-500 hover:text-red-700 font-medium"
                >
                  Clear
                </button>
              </div>
            )}

            {fileError && (
              <p className="mt-1 text-sm text-red-600 font-medium">{fileError}</p>
            )}
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 text-white font-medium px-6 py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors cursor-pointer"
            >
              {saving ? 'Uploading Document...' : 'Upload Document'}
            </button>
          </div>
        </form>
      )}

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">
            {isMentor ? 'Your Uploaded Resources' : 'Available Learning Resources'}
          </h2>
          <span className="text-sm text-gray-500 font-medium">
            {resources.length} {resources.length === 1 ? 'document' : 'documents'}
          </span>
        </div>

        {resources.length === 0 ? (
          <div className="bg-white rounded-xl p-8 text-center border border-gray-200 shadow-sm">
            <div className="text-4xl mb-3">📚</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-1">
              No Resources Available
            </h3>
            <p className="text-gray-500 text-sm max-w-md mx-auto">
              {isMentor
                ? 'You have not uploaded any learning documents yet. Use the form above to share documents with your mentees.'
                : 'No documents have been shared by your mentor yet. Check back soon!'}
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
                  className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-lg font-bold text-gray-900 leading-snug">
                        {resource.title}
                      </h3>
                      <span
                        className={`text-xs px-2.5 py-1 rounded-full font-semibold border flex items-center gap-1 shrink-0 ${badge.bg}`}
                      >
                        <span>{badge.icon}</span>
                        <span>{badge.label}</span>
                      </span>
                    </div>

                    {resource.description && (
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {resource.description}
                      </p>
                    )}

                    <div className="text-xs text-gray-500 space-y-1 pt-1">
                      {resource.file_name && (
                        <p className="truncate">
                          <span className="font-semibold text-gray-700">File:</span>{' '}
                          {resource.file_name}
                        </p>
                      )}

                      {!isMentor && resource.mentor && (
                        <p>
                          <span className="font-semibold text-gray-700">Shared by:</span>{' '}
                          {resource.mentor.name || 'Your Mentor'}
                        </p>
                      )}

                      {isMentor && (
                        <p>
                          <span className="font-semibold text-gray-700">Target:</span>{' '}
                          {resource.mentee
                            ? `Shared with ${resource.mentee.name}`
                            : 'Shared with all mentees'}
                        </p>
                      )}

                      {resource.created_at && (
                        <p>
                          <span className="font-semibold text-gray-700">Uploaded:</span>{' '}
                          {new Date(resource.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-gray-100 flex items-center justify-between gap-2">
                    <button
                      onClick={() => handleDownload(resource)}
                      disabled={isDownloading}
                      className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 hover:bg-blue-100 px-4 py-2 rounded-lg font-medium text-sm transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      <span>⬇</span>
                      <span>{isDownloading ? 'Downloading...' : 'Download / Open'}</span>
                    </button>

                    {isMentor && (
                      <button
                        onClick={() => handleDelete(resource.id)}
                        disabled={isDeleting}
                        className="text-xs text-red-500 hover:text-red-700 font-medium px-2 py-1 rounded hover:bg-red-50 transition-colors disabled:opacity-50 cursor-pointer"
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