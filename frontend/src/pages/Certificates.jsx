import { useEffect, useState, useRef } from 'react'
import api from '../services/api'

function Certificates() {
  const token = localStorage.getItem('token')

  const [certificates, setCertificates] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [downloadingId, setDownloadingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  // Form states
  const [title, setTitle] = useState('')
  const [issuer, setIssuer] = useState('')
  const [issueDate, setIssueDate] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)

  // Feedback states
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [fileError, setFileError] = useState('')

  const fileInputRef = useRef(null)

  const ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']
  const MAX_FILE_SIZE_MB = 16

  const fetchCertificates = async () => {
    try {
      const response = await api.get('/certificates', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setCertificates(response.data.certificates || [])
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load certificates.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCertificates()
  }, [])

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    setFileError('')
    if (!file) {
      setSelectedFile(null)
      return
    }

    const ext = file.name.split('.').pop().toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setFileError(`Invalid file format (.${ext}). Allowed types: PDF (.pdf), JPG (.jpg, .jpeg), PNG (.png)`)
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
      setFileError('Please select a certificate document/image to upload.')
      return
    }

    try {
      setUploading(true)
      setMessage('')
      setError('')
      setFileError('')

      const formData = new FormData()
      formData.append('title', title.trim())
      formData.append('issuer', issuer.trim())
      formData.append('issue_date', issueDate)
      formData.append('file', selectedFile)

      await api.post('/certificates', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      })

      setMessage('Certificate uploaded successfully!')

      setTitle('')
      setIssuer('')
      setIssueDate('')
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      fetchCertificates()
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to upload certificate.')
    } finally {
      setUploading(false)
    }
  }

  const handleDownload = async (cert) => {
    try {
      setDownloadingId(cert.id)
      setError('')

      const response = await api.get(`/certificates/${cert.id}/download`, {
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

      const fileName = cert.file_name || `${cert.title || 'certificate'}`
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to download certificate.')
    } finally {
      setDownloadingId(null)
    }
  }

  const handleDelete = async (certId) => {
    if (!window.confirm('Are you sure you want to delete this certificate?')) {
      return
    }

    try {
      setDeletingId(certId)
      await api.delete(`/certificates/${certId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setMessage('Certificate deleted successfully.')
      fetchCertificates()
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete certificate.')
    } finally {
      setDeletingId(null)
    }
  }

  const getBadgeStyle = (fileType) => {
    const type = (fileType || '').toLowerCase()
    if (type === 'pdf') {
      return { label: 'PDF Document', bg: 'bg-red-100 text-red-800 border-red-200', icon: '📄' }
    }
    return { label: 'Image Badge', bg: 'bg-blue-100 text-blue-800 border-blue-200', icon: '🖼️' }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-gray-500 font-medium">Loading certificates...</p>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Certificates</h1>
        <p className="text-gray-600 mt-1">
          Upload, manage, and download your earned professional credentials and course completion certificates.
        </p>
      </div>

      {/* Alert Messages */}
      {message && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage('')} className="text-green-700 font-bold ml-4 hover:opacity-75">
            ×
          </button>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-red-700 font-bold ml-4 hover:opacity-75">
            ×
          </button>
        </div>
      )}

      {/* Upload Certificate Form */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 space-y-5"
      >
        <div className="border-b border-gray-100 pb-3">
          <h2 className="text-lg font-bold text-gray-900">Upload New Certificate</h2>
          <p className="text-sm text-gray-500">
            Supported formats: PDF (.pdf), JPG (.jpg, .jpeg), PNG (.png) up to 16MB.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Certificate Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={200}
              placeholder="e.g. AWS Certified Solutions Architect"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Issuer / Institution <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={issuer}
              onChange={(e) => setIssuer(e.target.value)}
              required
              maxLength={200}
              placeholder="e.g. Amazon Web Services, Coursera"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Issue Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={issueDate}
              onChange={(e) => setIssueDate(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Certificate Document / Image <span className="text-red-500">*</span>
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFileChange}
            required
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
          />

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

          {fileError && <p className="mt-1 text-sm text-red-600 font-medium">{fileError}</p>}
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={uploading}
            className="bg-blue-600 text-white font-medium px-6 py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors cursor-pointer"
          >
            {uploading ? 'Uploading Certificate...' : 'Upload Certificate'}
          </button>
        </div>
      </form>

      {/* Certificates Cards */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">Your Earned Certificates</h2>
          <span className="text-sm text-gray-500 font-medium">
            {certificates.length} {certificates.length === 1 ? 'certificate' : 'certificates'}
          </span>
        </div>

        {certificates.length === 0 ? (
          <div className="bg-white rounded-xl p-8 text-center border border-gray-200 shadow-sm">
            <div className="text-4xl mb-3">🎓</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-1">No Certificates Uploaded Yet</h3>
            <p className="text-gray-500 text-sm max-w-md mx-auto">
              Add your credentials, certifications, or course completion records above to build your portfolio.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {certificates.map((cert) => {
              const badge = getBadgeStyle(cert.file_type)
              const isDownloading = downloadingId === cert.id
              const isDeleting = deletingId === cert.id

              return (
                <div
                  key={cert.id}
                  className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-lg font-bold text-gray-900 leading-snug">
                        {cert.title}
                      </h3>
                      <span
                        className={`text-xs px-2.5 py-1 rounded-full font-semibold border flex items-center gap-1 shrink-0 ${badge.bg}`}
                      >
                        <span>{badge.icon}</span>
                        <span>{badge.label}</span>
                      </span>
                    </div>

                    <div className="text-sm text-gray-600 space-y-1">
                      <p>
                        <span className="font-semibold text-gray-700">Issuer:</span> {cert.issuer}
                      </p>
                      <p>
                        <span className="font-semibold text-gray-700">Issue Date:</span>{' '}
                        {cert.issue_date ? new Date(cert.issue_date).toLocaleDateString() : 'N/A'}
                      </p>
                      {cert.file_name && (
                        <p className="text-xs text-gray-500 truncate pt-1">
                          <span className="font-semibold text-gray-700">File:</span> {cert.file_name}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-gray-100 flex items-center justify-between gap-2">
                    <button
                      onClick={() => handleDownload(cert)}
                      disabled={isDownloading}
                      className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 hover:bg-blue-100 px-4 py-2 rounded-lg font-medium text-sm transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      <span>⬇</span>
                      <span>{isDownloading ? 'Downloading...' : 'View / Download'}</span>
                    </button>

                    <button
                      onClick={() => handleDelete(cert.id)}
                      disabled={isDeleting}
                      className="text-xs text-red-500 hover:text-red-700 font-medium px-2 py-1 rounded hover:bg-red-50 transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      {isDeleting ? 'Deleting...' : 'Delete'}
                    </button>
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

export default Certificates
