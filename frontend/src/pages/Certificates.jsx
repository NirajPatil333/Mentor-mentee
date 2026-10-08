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
      return { label: 'PDF Document', bg: 'bg-rose-50 text-rose-700 border-rose-200/80' }
    }
    return { label: 'Image', bg: 'bg-purple-50 text-purple-700 border-purple-200/80' }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading certificates...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Certificates</h1>
        <p className="text-slate-500 text-sm mt-1">
          Upload, manage, and download your earned professional credentials and course completion certificates.
        </p>
      </div>

      {message && (
        <div className="bg-emerald-50 border border-emerald-200/80 text-emerald-700 px-4 py-3 rounded-lg flex justify-between items-center text-sm font-medium">
          <span>{message}</span>
          <button onClick={() => setMessage('')} className="text-emerald-700 font-bold ml-4 hover:opacity-75 cursor-pointer">
            ×
          </button>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200/80 text-rose-700 px-4 py-3 rounded-lg flex justify-between items-center text-sm font-medium">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-rose-700 font-bold ml-4 hover:opacity-75 cursor-pointer">
            ×
          </button>
        </div>
      )}

      {/* Upload Form */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 space-y-5"
      >
        <div className="border-b border-slate-100 pb-3">
          <h2 className="text-lg font-bold text-slate-900">Upload New Certificate</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Supported formats: PDF (.pdf), JPG (.jpg, .jpeg), PNG (.png) up to 16MB.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Certificate Title <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={200}
              placeholder="e.g. AWS Certified Solutions Architect"
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Issuer / Institution <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={issuer}
              onChange={(e) => setIssuer(e.target.value)}
              required
              maxLength={200}
              placeholder="e.g. Amazon Web Services"
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Issue Date <span className="text-rose-500">*</span>
            </label>
            <input
              type="date"
              value={issueDate}
              onChange={(e) => setIssueDate(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">
            Certificate Document / Image <span className="text-rose-500">*</span>
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFileChange}
            required
            className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100 cursor-pointer"
          />

          {selectedFile && (
            <div className="mt-2 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-800">Selected file:</span>{' '}
                <span className="text-purple-600 font-semibold">{selectedFile.name}</span>{' '}
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

          {fileError && <p className="mt-1 text-xs text-rose-600 font-semibold">{fileError}</p>}
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={uploading}
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-xs disabled:opacity-50 cursor-pointer text-sm"
          >
            {uploading ? 'Uploading Certificate...' : 'Upload Certificate'}
          </button>
        </div>
      </form>

      {/* Certificates Cards */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-900">Your Earned Certificates</h2>
          <span className="text-xs text-slate-500 font-medium">
            {certificates.length} {certificates.length === 1 ? 'certificate' : 'certificates'}
          </span>
        </div>

        {certificates.length === 0 ? (
          <div className="bg-white rounded-xl p-8 border border-slate-200/80 shadow-xs text-center py-12">
            <div className="w-12 h-12 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-800">No Certificates Uploaded Yet</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Add your course completion credentials or certificates above to showcase your portfolio.
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
                  className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs hover:border-slate-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-base font-bold text-slate-900 leading-snug">
                        {cert.title}
                      </h3>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border shrink-0 ${badge.bg}`}
                      >
                        {badge.label}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 space-y-1 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <p>
                        <span className="font-semibold text-slate-700">Issuer:</span> {cert.issuer}
                      </p>
                      <p>
                        <span className="font-semibold text-slate-700">Issue Date:</span>{' '}
                        {cert.issue_date ? new Date(cert.issue_date).toLocaleDateString() : 'N/A'}
                      </p>
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                    <button
                      onClick={() => handleDownload(cert)}
                      disabled={isDownloading}
                      className="inline-flex items-center gap-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 font-medium px-3.5 py-1.5 rounded-lg text-xs transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      <span>{isDownloading ? 'Downloading...' : 'View / Download'}</span>
                    </button>

                    <button
                      onClick={() => handleDelete(cert.id)}
                      disabled={isDeleting}
                      className="text-xs text-rose-600 hover:text-rose-800 font-medium px-2.5 py-1 rounded-lg hover:bg-rose-50 transition-colors disabled:opacity-50 cursor-pointer"
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
