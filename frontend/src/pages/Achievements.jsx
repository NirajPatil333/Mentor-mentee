import { useEffect, useState } from 'react'
import api from '../services/api'

function Achievements() {
  const token = localStorage.getItem('token')

  const [achievements, setAchievements] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  // Form states
  const [editingId, setEditingId] = useState(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [achievementDate, setAchievementDate] = useState('')
  const [achievementUrl, setAchievementUrl] = useState('')

  // Feedback states
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const fetchAchievements = async () => {
    try {
      const response = await api.get('/achievements', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setAchievements(response.data.achievements || [])
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load achievements.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAchievements()
  }, [])

  const resetForm = () => {
    setEditingId(null)
    setTitle('')
    setDescription('')
    setAchievementDate('')
    setAchievementUrl('')
  }

  const handleEdit = (ach) => {
    setEditingId(ach.id)
    setTitle(ach.title || '')
    setDescription(ach.description || '')
    setAchievementDate(ach.achievement_date || '')
    setAchievementUrl(ach.achievement_url || '')
    setMessage('')
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!title.trim()) {
      setError('Please provide an achievement title.')
      return
    }

    if (!achievementDate) {
      setError('Please select an achievement date.')
      return
    }

    try {
      setSaving(true)
      setMessage('')
      setError('')

      const payload = {
        title: title.trim(),
        description: description.trim() || null,
        achievement_date: achievementDate,
        achievement_url: achievementUrl.trim() || null,
      }

      if (editingId) {
        await api.put(`/achievements/${editingId}`, payload, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setMessage('Achievement updated successfully!')
      } else {
        await api.post('/achievements', payload, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setMessage('Achievement added successfully!')
      }

      resetForm()
      fetchAchievements()
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save achievement.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (achId) => {
    if (!window.confirm('Are you sure you want to delete this achievement?')) {
      return
    }

    try {
      setDeletingId(achId)
      await api.delete(`/achievements/${achId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setMessage('Achievement deleted successfully.')
      if (editingId === achId) resetForm()
      fetchAchievements()
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete achievement.')
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading achievements...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Achievements & Milestones</h1>
        <p className="text-slate-500 text-sm mt-1">
          Record and highlight your major accomplishments, competitions, and learning awards.
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

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 space-y-5"
      >
        <div className="flex justify-between items-center border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {editingId ? 'Edit Achievement' : 'Add New Achievement'}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Showcase hackathons, certifications, or major milestones.
            </p>
          </div>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 border border-slate-200 px-3 py-1 rounded-lg transition-colors cursor-pointer"
            >
              Cancel Edit
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Achievement Title <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={200}
              placeholder="e.g. 1st Place - Global AI Hackathon"
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Achievement Date <span className="text-rose-500">*</span>
            </label>
            <input
              type="date"
              value={achievementDate}
              onChange={(e) => setAchievementDate(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">
            Description & Impact (Optional)
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows="3"
            placeholder="Describe your accomplishment, technologies used, or key learnings..."
            className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">
            Project / Verification URL (Optional)
          </label>
          <input
            type="url"
            value={achievementUrl}
            onChange={(e) => setAchievementUrl(e.target.value)}
            placeholder="https://github.com/..., https://devpost.com/..."
            className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
          />
        </div>

        <div className="pt-2 flex items-center gap-3">
          <button
            type="submit"
            disabled={saving}
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-xs disabled:opacity-50 cursor-pointer text-sm"
          >
            {saving
              ? 'Saving...'
              : editingId
              ? 'Update Achievement'
              : 'Add Achievement'}
          </button>
        </div>
      </form>

      {/* Cards List */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-900">Your Achievements</h2>
          <span className="text-xs text-slate-500 font-medium">
            {achievements.length} {achievements.length === 1 ? 'achievement' : 'achievements'}
          </span>
        </div>

        {achievements.length === 0 ? (
          <div className="bg-white rounded-xl p-8 border border-slate-200/80 shadow-xs text-center py-12">
            <div className="w-12 h-12 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-800">No Achievements Recorded Yet</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Add your completed milestones or competition wins above to showcase your growth.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {achievements.map((ach) => {
              const isDeleting = deletingId === ach.id

              return (
                <div
                  key={ach.id}
                  className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs hover:border-slate-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-base font-bold text-slate-900 leading-snug">
                        {ach.title}
                      </h3>
                      <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold border bg-purple-50 text-purple-700 border-purple-200/80 shrink-0">
                        Achievement
                      </span>
                    </div>

                    {ach.description && (
                      <p className="text-xs text-slate-600 line-clamp-3">
                        {ach.description}
                      </p>
                    )}

                    <div className="text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      {ach.achievement_date && (
                        <p>
                          <span className="font-semibold text-slate-700">Date Attained:</span>{' '}
                          {new Date(ach.achievement_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                    <div>
                      {ach.achievement_url ? (
                        <a
                          href={ach.achievement_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs font-semibold hover:underline"
                        >
                          <span>Open Link</span>
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      ) : (
                        <span className="text-xs text-slate-400">No external link</span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleEdit(ach)}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(ach.id)}
                        disabled={isDeleting}
                        className="text-xs font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
                      >
                        {isDeleting ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
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

export default Achievements
