import { useEffect, useState } from 'react'
import api from '../services/api'

function Progress() {
  const user = JSON.parse(localStorage.getItem('user'))
  const isMentor = user?.role === 'mentor'
  const token = localStorage.getItem('token')

  const [progressList, setProgressList] = useState([])
  const [mentees, setMentees] = useState([])
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  // Form states
  const [editingId, setEditingId] = useState(null)
  const [menteeId, setMenteeId] = useState('')
  const [skillId, setSkillId] = useState('')
  const [goal, setGoal] = useState('')
  const [description, setDescription] = useState('')
  const [progressPercentage, setProgressPercentage] = useState(0)
  const [status, setStatus] = useState('not_started')

  // Feedback states
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const fetchProgress = async () => {
    try {
      const response = await api.get('/progress', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setProgressList(response.data.progress || [])
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load progress records.')
    } finally {
      setLoading(false)
    }
  }

  const fetchMenteesAndSkills = async () => {
    try {
      const [skillsRes, menteesRes] = await Promise.all([
        api.get('/skills'),
        isMentor ? api.get('/progress/mentees', { headers: { Authorization: `Bearer ${token}` } }) : Promise.resolve({ data: { mentees: [] } })
      ])
      setSkills(skillsRes.data.skills || [])
      if (isMentor) {
        const menteeList = menteesRes.data.mentees || []
        setMentees(menteeList)
        if (menteeList.length > 0 && !menteeId) {
          setMenteeId(menteeList[0].id)
        }
      }
      if (skillsRes.data.skills?.length > 0 && !skillId) {
        setSkillId(skillsRes.data.skills[0].id)
      }
    } catch {
      // Non-blocking fetch fallback
    }
  }

  useEffect(() => {
    fetchProgress()
    fetchMenteesAndSkills()
  }, [])

  const resetForm = () => {
    setEditingId(null)
    setGoal('')
    setDescription('')
    setProgressPercentage(0)
    setStatus('not_started')
    if (mentees.length > 0) setMenteeId(mentees[0].id)
    if (skills.length > 0) setSkillId(skills[0].id)
  }

  const handleEdit = (record) => {
    setEditingId(record.id)
    setMenteeId(record.mentee_id || (record.mentee?.id || ''))
    setSkillId(record.skill_id || (record.skill?.id || ''))
    setGoal(record.goal || '')
    setDescription(record.description || '')
    setProgressPercentage(record.progress_percentage || 0)
    setStatus(record.status || 'not_started')
    setMessage('')
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!goal.trim()) {
      setError('Please provide a learning goal title.')
      return
    }

    if (isMentor && !editingId && !menteeId) {
      setError('Please select a mentee.')
      return
    }

    if (!skillId) {
      setError('Please select a skill.')
      return
    }

    try {
      setSaving(true)
      setMessage('')
      setError('')

      const payload = {
        mentee_id: parseInt(menteeId),
        skill_id: parseInt(skillId),
        goal: goal.trim(),
        description: description.trim(),
        progress_percentage: parseInt(progressPercentage),
        status,
      }

      if (editingId) {
        await api.put(`/progress/${editingId}`, payload, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setMessage('Progress goal updated successfully!')
      } else {
        await api.post('/progress', payload, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setMessage('Progress goal created successfully!')
      }

      resetForm()
      fetchProgress()
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save progress record.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this progress goal?')) {
      return
    }

    try {
      setDeletingId(id)
      await api.delete(`/progress/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setMessage('Progress record deleted successfully.')
      if (editingId === id) resetForm()
      fetchProgress()
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete progress record.')
    } finally {
      setDeletingId(null)
    }
  }

  const getStatusBadge = (statusValue) => {
    switch (statusValue) {
      case 'completed':
        return {
          label: 'Completed',
          bg: 'bg-green-100 text-green-800 border-green-200',
          dot: 'bg-green-500',
        }
      case 'in_progress':
        return {
          label: 'In Progress',
          bg: 'bg-blue-100 text-blue-800 border-blue-200',
          dot: 'bg-blue-500',
        }
      case 'not_started':
      default:
        return {
          label: 'Not Started',
          bg: 'bg-gray-100 text-gray-700 border-gray-200',
          dot: 'bg-gray-400',
        }
    }
  }

  const getProgressBarColor = (percentage, statusValue) => {
    if (statusValue === 'completed' || percentage === 100) return 'bg-green-500'
    if (percentage > 50) return 'bg-blue-600'
    if (percentage > 0) return 'bg-amber-500'
    return 'bg-gray-300'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-gray-500 font-medium">Loading progress records...</p>
      </div>
    )
  }

  const totalGoals = progressList.length
  const completedGoals = progressList.filter((p) => p.status === 'completed' || p.progress_percentage === 100).length
  const inProgressGoals = progressList.filter((p) => p.status === 'in_progress' && p.progress_percentage < 100).length
  const avgProgress = totalGoals > 0 ? Math.round(progressList.reduce((acc, curr) => acc + (curr.progress_percentage || 0), 0) / totalGoals) : 0

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Page Title & Intro */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Progress Tracking</h1>
          <p className="text-gray-600 mt-1">
            {isMentor
              ? 'Assign and track skill milestones and goal progress for your mentees.'
              : 'Track your learning milestones, skill development, and mentor feedback.'}
          </p>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Total Goals</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{totalGoals}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">In Progress</p>
          <p className="text-2xl font-bold text-blue-700 mt-1">{inProgressGoals}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-green-600">Completed</p>
          <p className="text-2xl font-bold text-green-700 mt-1">{completedGoals}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-purple-600">Avg Completion</p>
          <p className="text-2xl font-bold text-purple-700 mt-1">{avgProgress}%</p>
        </div>
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

      {/* Mentor Progress Goal Form (Create / Edit) */}
      {isMentor && (
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 space-y-5"
        >
          <div className="flex justify-between items-center border-b border-gray-100 pb-3">
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                {editingId ? 'Edit Progress Goal' : 'Create New Learning Milestone'}
              </h2>
              <p className="text-sm text-gray-500">
                {editingId
                  ? 'Update completion percentage, goal notes, or milestone status.'
                  : 'Assign a targeted goal with skill association for your accepted mentee.'}
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
            {/* Mentee Selector */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Mentee <span className="text-red-500">*</span>
              </label>
              <select
                value={menteeId}
                onChange={(e) => setMenteeId(e.target.value)}
                disabled={Boolean(editingId) || mentees.length === 0}
                required
                className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:bg-gray-100"
              >
                {mentees.length === 0 ? (
                  <option value="">No accepted mentees found</option>
                ) : (
                  mentees.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.email})
                    </option>
                  ))
                )}
              </select>
              {mentees.length === 0 && (
                <p className="text-xs text-amber-600 mt-1">
                  You can only track progress for mentees with an accepted mentorship request.
                </p>
              )}
            </div>

            {/* Skill Selector */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Skill Area <span className="text-red-500">*</span>
              </label>
              <select
                value={skillId}
                onChange={(e) => setSkillId(e.target.value)}
                required
                className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                {skills.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.category})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Goal Title */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Learning Goal / Milestone Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              required
              maxLength={255}
              placeholder="e.g. Master Flask REST Blueprints & SQLAlchemy ORM"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Description / Action Steps (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows="2"
              placeholder="Detail specific tasks, assignments, or success criteria..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Progress Percentage Slider */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-sm font-semibold text-gray-700">
                  Progress Percentage
                </label>
                <span className="text-sm font-bold text-blue-600">
                  {progressPercentage}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={progressPercentage}
                onChange={(e) => {
                  const val = parseInt(e.target.value)
                  setProgressPercentage(val)
                  if (val === 100) setStatus('completed')
                  else if (val > 0 && status === 'not_started') setStatus('in_progress')
                }}
                className="w-full cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                <span>0% (Not Started)</span>
                <span>50% (Halfway)</span>
                <span>100% (Completed)</span>
              </div>
            </div>

            {/* Status Dropdown */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => {
                  const newStatus = e.target.value
                  setStatus(newStatus)
                  if (newStatus === 'completed' && progressPercentage < 100) {
                    setProgressPercentage(100)
                  } else if (newStatus === 'not_started') {
                    setProgressPercentage(0)
                  }
                }}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="not_started">Not Started</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>

          <div className="pt-2 flex items-center gap-3">
            <button
              type="submit"
              disabled={saving || (isMentor && mentees.length === 0)}
              className="bg-blue-600 text-white font-medium px-6 py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors cursor-pointer"
            >
              {saving
                ? 'Saving...'
                : editingId
                ? 'Update Progress Goal'
                : 'Create Progress Goal'}
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
      )}

      {/* Progress Records List */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">
            {isMentor ? 'Managed Progress Milestones' : 'My Learning Milestones'}
          </h2>
          <span className="text-sm text-gray-500 font-medium">
            {progressList.length} {progressList.length === 1 ? 'record' : 'records'}
          </span>
        </div>

        {progressList.length === 0 ? (
          <div className="bg-white rounded-xl p-8 text-center border border-gray-200 shadow-sm">
            <div className="text-4xl mb-3">📈</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-1">
              No Progress Records Yet
            </h3>
            <p className="text-gray-500 text-sm max-w-md mx-auto">
              {isMentor
                ? 'You have not created any progress goals for your mentees yet. Use the form above to track their milestone achievements.'
                : 'Your mentor has not set up any progress milestones yet. Once created, you will see your learning path and goals here.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {progressList.map((item) => {
              const badge = getStatusBadge(item.status)
              const barColor = getProgressBarColor(item.progress_percentage, item.status)
              const isDeleting = deletingId === item.id

              return (
                <div
                  key={item.id}
                  className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    {/* Header: Skill tag + Status */}
                    <div className="flex items-start justify-between gap-2">
                      {item.skill && (
                        <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100">
                          {item.skill.name} • {item.skill.category}
                        </span>
                      )}
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border inline-flex items-center gap-1.5 shrink-0 ${badge.bg}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`}></span>
                        <span>{badge.label}</span>
                      </span>
                    </div>

                    {/* Goal Title */}
                    <h3 className="text-lg font-bold text-gray-900 leading-snug">
                      {item.goal}
                    </h3>

                    {/* Description */}
                    {item.description && (
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {item.description}
                      </p>
                    )}

                    {/* Progress Bar */}
                    <div className="space-y-1.5 pt-1">
                      <div className="flex justify-between items-center text-xs font-semibold">
                        <span className="text-gray-600">Completion</span>
                        <span className="text-gray-900">{item.progress_percentage}%</span>
                      </div>
                      <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden border border-gray-200">
                        <div
                          className={`h-full ${barColor} transition-all duration-300 rounded-full`}
                          style={{ width: `${Math.min(100, Math.max(0, item.progress_percentage))}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Metadata Footer */}
                    <div className="text-xs text-gray-500 space-y-1 pt-2 border-t border-gray-50">
                      {isMentor && item.mentee && (
                        <p>
                          <span className="font-semibold text-gray-700">Mentee:</span>{' '}
                          {item.mentee.name || 'Assigned Mentee'} ({item.mentee.email || ''})
                        </p>
                      )}
                      {!isMentor && item.mentor && (
                        <p>
                          <span className="font-semibold text-gray-700">Assigned by Mentor:</span>{' '}
                          {item.mentor.name || 'Your Mentor'}
                        </p>
                      )}
                      {item.updated_at && (
                        <p>
                          <span className="font-semibold text-gray-700">Last Updated:</span>{' '}
                          {new Date(item.updated_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Mentor Actions */}
                  {isMentor && (
                    <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleEdit(item)}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        disabled={isDeleting}
                        className="text-xs font-semibold text-red-600 hover:text-red-800 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
                      >
                        {isDeleting ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default Progress
