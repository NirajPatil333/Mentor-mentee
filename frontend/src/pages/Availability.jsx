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
    return <p className="text-gray-500">Loading availability schedule...</p>
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
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Weekly Availability</h1>
        <p className="mt-2 text-gray-600">
          Configure your recurring weekly availability slots for mentorship sessions.
        </p>
      </div>

      {message && (
        <div className="p-4 bg-green-50 text-green-700 rounded-lg border border-green-200">
          {message}
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {/* Add Slot Form */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Add Recurring Slot</h2>

        <form onSubmit={handleAddSlot} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Day of Week</label>
            <select
              value={selectedDay}
              onChange={(e) => setSelectedDay(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {DAYS_OF_WEEK.map(day => (
                <option key={day} value={day}>{day}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Start Time</label>
            <input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">End Time</label>
            <input
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white font-medium py-2.5 px-4 rounded-lg hover:bg-blue-700 transition text-sm"
            >
              Add Slot
            </button>
          </div>
        </form>
      </div>

      {/* Weekly Schedule Display */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">Current Weekly Slots</h2>
          <button
            onClick={handleSaveAvailability}
            disabled={saving}
            className="bg-emerald-600 text-white font-semibold px-6 py-2.5 rounded-lg hover:bg-emerald-700 transition disabled:opacity-50 text-sm"
          >
            {saving ? 'Saving...' : 'Save Availability'}
          </button>
        </div>

        {availabilitySlots.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No availability slots defined.</p>
            <p className="text-xs text-gray-400 mt-1">Use the form above to add your weekly availability.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {DAYS_OF_WEEK.map(day => {
              const daySlots = slotsByDay[day] || []
              return (
                <div key={day} className="border border-gray-200 rounded-xl p-4 bg-gray-50/50">
                  <h3 className="font-bold text-gray-900 border-b border-gray-200 pb-2 mb-3">
                    {day}
                  </h3>

                  {daySlots.length === 0 ? (
                    <p className="text-xs text-gray-400 italic py-2">Unavailable</p>
                  ) : (
                    <div className="space-y-2">
                      {daySlots.map(slot => (
                        <div
                          key={slot.originalIndex}
                          className="bg-white border border-gray-200 rounded-lg p-3 flex justify-between items-center shadow-xs"
                        >
                          <div>
                            <p className="text-sm font-semibold text-gray-800">
                              {slot.start_time?.slice(0, 5)} - {slot.end_time?.slice(0, 5)}
                            </p>
                          </div>
                          <button
                            onClick={() => handleRemoveSlot(slot.originalIndex)}
                            className="text-xs text-red-600 hover:text-red-800 font-medium px-2 py-1 rounded hover:bg-red-50 transition"
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
