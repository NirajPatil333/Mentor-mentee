import { useEffect, useState } from 'react'
import api from '../services/api'

const DAYS_OF_WEEK = [
  'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]

function Availability() {
  const [availabilitySlots, setAvailabilitySlots] = useState([])
  const [selectedDay, setSelectedDay] = useState('Monday')
  const [startTime, setStartTime] = useState('09:00')
  const [endTime, setEndTime] = useState('10:00')

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const fetchAvailability = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('token')

      const response = await api.get('/mentors/availability', {
        headers: { Authorization: `Bearer ${token}` }
      })

      setAvailabilitySlots(response.data.availability || [])
    } catch (err) {
      console.error('Failed to load availability:', err)
      setError(err.response?.data?.message || 'Failed to load availability slots.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAvailability()
  }, [])

  const handleAddSlot = (e) => {
    e.preventDefault()
    setMessage('')
    setError('')

    if (!startTime || !endTime) {
      setError('Please provide both start time and end time.')
      return
    }

    if (startTime >= endTime) {
      setError('Start time must be strictly earlier than end time.')
      return
    }

    const newSlot = {
      day_of_week: selectedDay,
      start_time: startTime.length === 5 ? `${startTime}:00` : startTime,
      end_time: endTime.length === 5 ? `${endTime}:00` : endTime
    }

    setAvailabilitySlots(prev => [...prev, newSlot])
    setMessage('Slot added locally. Click "Save Availability" to persist changes.')
  }

  const handleRemoveSlot = (indexToRemove) => {
    setMessage('')
    setError('')
    setAvailabilitySlots(prev => prev.filter((_, idx) => idx !== indexToRemove))
    setMessage('Slot removed locally. Click "Save Availability" to persist changes.')
  }

  const handleSaveAvailability = async () => {
    try {
      setSaving(true)
      setMessage('')
      setError('')
      const token = localStorage.getItem('token')

      const payload = {
        availability: availabilitySlots.map(slot => ({
          day_of_week: slot.day_of_week,
          start_time: slot.start_time,
          end_time: slot.end_time
        }))
      }

      const response = await api.put('/mentors/availability', payload, {
        headers: { Authorization: `Bearer ${token}` }
      })

      setMessage(response.data.message || 'Availability schedule saved successfully!')
      setAvailabilitySlots(response.data.availability || [])
    } catch (err) {
      console.error('Failed to save availability:', err)
      setError(err.response?.data?.message || 'Failed to save availability.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
        <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="font-medium text-sm">Loading availability schedule...</span>
      </div>
    )
  }

  const slotsByDay = {}
  DAYS_OF_WEEK.forEach(day => {
    slotsByDay[day] = []
  })
  availabilitySlots.forEach((slot, index) => {
    const matchedDay = DAYS_OF_WEEK.find(d => d.toLowerCase() === (slot.day_of_week || '').toLowerCase()) || slot.day_of_week
    if (!slotsByDay[matchedDay]) {
      slotsByDay[matchedDay] = []
    }
    slotsByDay[matchedDay].push({ ...slot, originalIndex: index })
  })

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Weekly Availability</h1>
        <p className="text-slate-500 text-sm mt-1">
          Configure your recurring weekly availability slots for mentorship sessions.
        </p>
      </div>

      {message && (
        <div className="rounded-lg bg-emerald-50 border border-emerald-200/80 p-3.5 text-sm text-emerald-700 font-medium">
          {message}
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-rose-50 border border-rose-200/80 p-3.5 text-sm text-rose-700 font-medium">
          {error}
        </div>
      )}

      {/* Add Slot Form */}
      <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80">
        <h2 className="text-lg font-bold text-slate-900 mb-4">Add Recurring Slot</h2>

        <form onSubmit={handleAddSlot} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Day of Week</label>
            <select
              value={selectedDay}
              onChange={(e) => setSelectedDay(e.target.value)}
              className="w-full rounded-lg border border-slate-300 p-2.5 text-slate-900 bg-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm cursor-pointer"
            >
              {DAYS_OF_WEEK.map(day => (
                <option key={day} value={day}>{day}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Start Time</label>
            <input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full rounded-lg border border-slate-300 p-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">End Time</label>
            <input
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full rounded-lg border border-slate-300 p-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
            />
          </div>

          <div>
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 px-4 rounded-lg transition-all duration-200 shadow-xs text-sm cursor-pointer"
            >
              Add Slot
            </button>
          </div>
        </form>
      </div>

      {/* Weekly Schedule Display */}
      <div className="bg-white rounded-xl p-6 shadow-xs border border-slate-200/80 space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-900">Current Weekly Schedule</h2>
          <button
            onClick={handleSaveAvailability}
            disabled={saving}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-2.5 rounded-lg transition-all duration-200 disabled:opacity-50 text-sm shadow-xs cursor-pointer"
          >
            {saving ? 'Saving...' : 'Save Availability'}
          </button>
        </div>

        {availabilitySlots.length === 0 ? (
          <div className="text-center py-12 text-slate-500 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
            <p className="text-sm font-medium">No availability slots defined.</p>
            <p className="text-xs text-slate-400 mt-1">Use the form above to add your weekly availability.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {DAYS_OF_WEEK.map(day => {
              const daySlots = slotsByDay[day] || []
              return (
                <div key={day} className="border border-slate-200/80 rounded-xl p-4 bg-slate-50/50">
                  <h3 className="font-bold text-sm text-slate-900 border-b border-slate-200/80 pb-2 mb-3">
                    {day}
                  </h3>

                  {daySlots.length === 0 ? (
                    <p className="text-xs text-slate-400 italic py-2">Unavailable</p>
                  ) : (
                    <div className="space-y-2">
                      {daySlots.map(slot => (
                        <div
                          key={slot.originalIndex}
                          className="bg-white border border-slate-200/80 rounded-lg p-3 flex justify-between items-center shadow-xs"
                        >
                          <div>
                            <p className="text-xs font-semibold text-slate-800">
                              {slot.start_time?.slice(0, 5)} - {slot.end_time?.slice(0, 5)}
                            </p>
                          </div>
                          <button
                            onClick={() => handleRemoveSlot(slot.originalIndex)}
                            className="text-xs text-rose-600 hover:text-rose-800 font-semibold px-2 py-1 rounded hover:bg-rose-50 transition cursor-pointer"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
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

export default Availability
