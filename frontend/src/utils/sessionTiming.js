/**
 * Calculates session timing state derived from scheduled_date, start_time, end_time, and status.
 * Compares against local browser time without mutating backend database records.
 */
export function getSessionTimingState(session) {
  if (!session) {
    return {
      timingState: 'past',
      isUpcoming: false,
      isOngoing: false,
      isPast: true,
      isCancelled: false,
      showJoinMeeting: false,
      displayStatus: 'Completed',
      badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200/80'
    }
  }

  const status = (session.status || '').toLowerCase()
  if (status === 'cancelled') {
    return {
      timingState: 'cancelled',
      isUpcoming: false,
      isOngoing: false,
      isPast: false,
      isCancelled: true,
      showJoinMeeting: false,
      displayStatus: 'Cancelled',
      badgeClass: 'bg-rose-50 text-rose-700 border-rose-200/80'
    }
  }

  const now = new Date()

  if (!session.scheduled_date) {
    const isComp = status === 'completed'
    return {
      timingState: isComp ? 'past' : 'upcoming',
      isUpcoming: !isComp,
      isOngoing: false,
      isPast: isComp,
      isCancelled: false,
      showJoinMeeting: Boolean(!isComp && session.meeting_url),
      displayStatus: isComp ? 'Completed' : 'Scheduled',
      badgeClass: isComp ? 'bg-emerald-50 text-emerald-700 border-emerald-200/80' : 'bg-blue-50 text-blue-700 border-blue-200/80'
    }
  }

  // Parse YYYY-MM-DD in local browser time
  const dateParts = String(session.scheduled_date).split('-').map(Number)
  if (dateParts.length < 3 || dateParts.some(isNaN)) {
    return {
      timingState: 'upcoming',
      isUpcoming: true,
      isOngoing: false,
      isPast: false,
      isCancelled: false,
      showJoinMeeting: Boolean(session.meeting_url),
      displayStatus: session.status || 'Scheduled',
      badgeClass: 'bg-blue-50 text-blue-700 border-blue-200/80'
    }
  }

  const [year, month, day] = dateParts

  let startH = 0, startM = 0
  if (session.start_time) {
    const sParts = String(session.start_time).split(':').map(Number)
    if (!isNaN(sParts[0])) startH = sParts[0]
    if (!isNaN(sParts[1])) startM = sParts[1]
  }

  let endH = 23, endM = 59
  let hasEndTime = false
  if (session.end_time) {
    const eParts = String(session.end_time).split(':').map(Number)
    if (!isNaN(eParts[0])) {
      endH = eParts[0]
      hasEndTime = true
    }
    if (!isNaN(eParts[1])) endM = eParts[1]
  } else if (session.start_time) {
    endH = (startH + 1) % 24
    endM = startM
    hasEndTime = true
  }

  const startDateTime = new Date(year, month - 1, day, startH, startM, 0)
  let endDateTime = new Date(year, month - 1, day, endH, endM, 59)

  if (hasEndTime && endDateTime < startDateTime) {
    endDateTime.setDate(endDateTime.getDate() + 1)
  }

  if (status === 'completed' || now > endDateTime) {
    return {
      timingState: 'past',
      isUpcoming: false,
      isOngoing: false,
      isPast: true,
      isCancelled: false,
      showJoinMeeting: false,
      displayStatus: 'Completed',
      badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200/80'
    }
  }

  if (now >= startDateTime && now <= endDateTime) {
    return {
      timingState: 'ongoing',
      isUpcoming: false,
      isOngoing: true,
      isPast: false,
      isCancelled: false,
      showJoinMeeting: Boolean(session.meeting_url),
      displayStatus: 'Ongoing',
      badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200/80'
    }
  }

  return {
    timingState: 'upcoming',
    isUpcoming: true,
    isOngoing: false,
    isPast: false,
    isCancelled: false,
    showJoinMeeting: Boolean(session.meeting_url),
    displayStatus: 'Scheduled',
    badgeClass: 'bg-blue-50 text-blue-700 border-blue-200/80'
  }
}
