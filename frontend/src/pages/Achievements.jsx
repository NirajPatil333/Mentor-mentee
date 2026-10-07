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
      <div className="flex items-center justify-center p-12">
        <p className="text-gray-500 font-medium">Loading achievements...</p>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Achievements & Milestones</h1>
        <p className="text-gray-600 mt-1">
          Record and highlight your major achievements, hackathon victories, open-source projects, and learning awards.
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

      {/* Add / Edit Achievement Form */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 space-y-5"
      >
        <div className="flex justify-between items-center border-b border-gray-100 pb-3">
          <div>
            <h2 className="text-lg font-bold text-gray-900">
              {editingId ? 'Edit Achievement' : 'Add New Achievement'}
            </h2>
            <p className="text-sm text-gray-500">
              Showcase projects, competitions, leadership recognitions, or major milestone accomplishments.
            </p>
          </div>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="text-sm font-medium text-gray-600 hover:text-gray-900 border px-3 py-1 rounded-lg"
            >
              Cancel Edit
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Achievement Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={200}
              placeholder="e.g. 1st Place - Global AI Hackathon"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Achievement Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={achievementDate}
              onChange={(e) => setAchievementDate(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Description & Impact (Optional)
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows="3"
            placeholder="Describe your accomplishment, technologies used, or team leadership..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Project / Verification URL (Optional)
          </label>
          <input
            type="url"
            value={achievementUrl}
            onChange={(e) => setAchievementUrl(e.target.value)}
            placeholder="https://github.com/..., https://devpost.com/..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <div className="pt-2 flex items-center gap-3">
          <button
            type="submit"
            disabled={saving}
            className="bg-blue-600 text-white font-medium px-6 py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors cursor-pointer"
          >
            {saving
              ? 'Saving...'
              : editingId
              ? 'Update Achievement'
              : 'Add Achievement'}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="px-4 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {/* Achievements Cards */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">Your Achievements</h2>
          <span className="text-sm text-gray-500 font-medium">
            {achievements.length} {achievements.length === 1 ? 'achievement' : 'achievements'}
          </span>
        </div>

        {achievements.length === 0 ? (
          <div className="bg-white rounded-xl p-8 text-center border border-gray-200 shadow-sm">
            <div className="text-4xl mb-3">🏆</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-1">No Achievements Recorded Yet</h3>
            <p className="text-gray-500 text-sm max-w-md mx-auto">
              Add your completed milestones, competition wins, and projects above to showcase your growth.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {achievements.map((ach) => {
              const isDeleting = deletingId === ach.id

              return (
                <div
                  key={ach.id}
                  className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-lg font-bold text-gray-900 leading-snug">
                        {ach.title}
                      </h3>
                      <span className="text-xs px-2.5 py-1 rounded-full font-semibold border bg-amber-50 text-amber-800 border-amber-200 flex items-center gap-1 shrink-0">
                        <span>🏆</span>
                        <span>Achievement</span>
                      </span>
                    </div>

                    {ach.description && (
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {ach.description}
                      </p>
                    )}

                    <div className="text-xs text-gray-500 space-y-1 pt-1">
                      {ach.achievement_date && (
                        <p>
                          <span className="font-semibold text-gray-700">Date Attained:</span>{' '}
                          {new Date(ach.achievement_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-gray-100 flex items-center justify-between gap-2">
                    <div>
                      {ach.achievement_url ? (
                        <a
                          href={ach.achievement_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-blue-600 hover:text-blue-800 text-sm font-semibold hover:underline"
                        >
                          <span>Open Link</span>
                          <span>↗</span>
                        </a>
                      ) : (
                        <span className="text-xs text-gray-400">No external link</span>
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
                        className="text-xs font-semibold text-red-600 hover:text-red-800 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
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
