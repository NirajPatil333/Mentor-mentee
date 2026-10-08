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
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
          dot: 'bg-emerald-500',
        }
      case 'in_progress':
        return {
          label: 'In Progress',
          bg: 'bg-blue-50 text-blue-700 border-blue-200/80',
          dot: 'bg-blue-500',
        }
      case 'not_started':
      default:
        return {
          label: 'Not Started',
          bg: 'bg-slate-100 text-slate-600 border-slate-200',
          dot: 'bg-slate-400',
        }
    }
  }

  const getProgressBarColor = (percentage, statusValue) => {
    if (statusValue === 'completed' || percentage === 100) return 'bg-emerald-500'
    if (percentage > 50) return 'bg-blue-600'
    if (percentage > 0) return 'bg-amber-500'
    return 'bg-slate-300'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading progress records...</span>
      </div>
    )
  }

  const totalGoals = progressList.length
  const completedGoals = progressList.filter((p) => p.status === 'completed' || p.progress_percentage === 100).length
  const inProgressGoals = progressList.filter((p) => p.status === 'in_progress' && p.progress_percentage < 100).length
  const avgProgress = totalGoals > 0 ? Math.round(progressList.reduce((acc, curr) => acc + (curr.progress_percentage || 0), 0) / totalGoals) : 0

  return (
    <div className="space-y-6">
      {/* Page Title & Intro */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Progress Tracking</h1>
        <p className="text-slate-500 text-sm mt-1">
          {isMentor
            ? 'Assign and track skill milestones and goal progress for your mentees.'
            : 'Track your learning milestones, skill development, and progress goals.'}
        </p>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Goals</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{totalGoals}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">In Progress</p>
          <p className="text-2xl font-bold text-blue-700 mt-1">{inProgressGoals}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">Completed</p>
          <p className="text-2xl font-bold text-emerald-700 mt-1">{completedGoals}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <p className="text-xs font-semibold uppercase tracking-wider text-purple-600">Avg Completion</p>
          <p className="text-2xl font-bold text-purple-700 mt-1">{avgProgress}%</p>
        </div>
      </div>

      {/* Alert Messages */}
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

      {/* Mentor Progress Goal Form */}
      {isMentor && (
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 space-y-5"
        >
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {editingId ? 'Edit Progress Goal' : 'Create New Learning Milestone'}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {editingId
                  ? 'Update completion percentage, goal notes, or milestone status.'
                  : 'Assign a targeted goal with skill association for your accepted mentee.'}
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
                Mentee <span className="text-rose-500">*</span>
              </label>
              <select
                value={menteeId}
                onChange={(e) => setMenteeId(e.target.value)}
                disabled={Boolean(editingId) || mentees.length === 0}
                required
                className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer disabled:bg-slate-100"
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
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Skill Area <span className="text-rose-500">*</span>
              </label>
              <select
                value={skillId}
                onChange={(e) => setSkillId(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer"
              >
                {skills.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.category})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Learning Goal / Milestone Title <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              required
              maxLength={255}
              placeholder="e.g. Master Flask REST Blueprints & SQLAlchemy ORM"
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Description / Action Steps (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows="2"
              placeholder="Detail specific tasks, assignments, or success criteria..."
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-sm font-semibold text-slate-700">
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
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
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
                className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer"
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
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-xs disabled:opacity-50 cursor-pointer text-sm"
            >
              {saving
                ? 'Saving...'
                : editingId
                ? 'Update Progress Goal'
                : 'Create Progress Goal'}
            </button>
          </div>
        </form>
      )}

      {/* Progress Records List */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-900">
            {isMentor ? 'Managed Progress Milestones' : 'My Learning Milestones'}
          </h2>
          <span className="text-xs text-slate-500 font-medium">
            {progressList.length} {progressList.length === 1 ? 'record' : 'records'}
          </span>
        </div>

        {progressList.length === 0 ? (
          <div className="bg-white rounded-xl p-8 border border-slate-200/80 shadow-xs text-center py-12">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-800">
              No Progress Records Yet
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {isMentor
                ? 'You have not created any progress goals for your mentees yet.'
                : 'Your mentor has not set up any progress milestones yet.'}
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
                  className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs hover:border-slate-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      {item.skill && (
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-100">
                          {item.skill.name}
                        </span>
                      )}
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border flex items-center gap-1 shrink-0 ${badge.bg}`}
                      >
                        <span>{badge.label}</span>
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-slate-900 leading-snug">
                      {item.goal}
                    </h3>

                    {item.description && (
                      <p className="text-xs text-slate-600 line-clamp-3">
                        {item.description}
                      </p>
                    )}

                    <div className="space-y-1.5 pt-1">
                      <div className="flex justify-between items-center text-xs font-semibold">
                        <span className="text-slate-600">Completion</span>
                        <span className="text-slate-900">{item.progress_percentage}%</span>
                      </div>
                      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200/60">
                        <div
                          className={`h-full ${barColor} transition-all duration-300 rounded-full`}
                          style={{ width: `${Math.min(100, Math.max(0, item.progress_percentage))}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>

                  {isMentor && (
                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleEdit(item)}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        disabled={isDeleting}
                        className="text-xs font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
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
