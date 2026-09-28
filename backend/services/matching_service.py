"""
Mentor Matching Service.

This service provides a transparent, rule-based mentor recommendation algorithm.
It evaluates compatibility between a mentee's declared learning interests and
available mentors using a weighted multi-criteria scoring formula.

SCORING FORMULA:
Total Match Score = (Skill Match * 0.50) + (Experience * 0.20) + (Rating * 0.15) + (Availability * 0.15)

1. Skill Match (50% weight):
   Percentage of the mentee's targeted learning skills that the mentor possesses.
   Skill Match % = (|Mentee Interests ∩ Mentor Skills| / |Mentee Interests|) * 100
   If mentee has not yet selected any learning interests, this component defaults to 0.0.

2. Experience (20% weight):
   Evaluates years of professional experience, linearly normalized against a 10-year benchmark.
   Experience % = min(max(experience_years, 0) / 10.0, 1.0) * 100

3. Rating (15% weight):
   Evaluates the mentor's average performance rating (0.0 to 5.0 scale).
   If reviews exist: Rating % = min(average_rating / 5.0, 1.0) * 100
   If no reviews yet: Defaults to a neutral baseline score of 50.0.

4. Availability (15% weight):
   Evaluates active recurring weekly mentoring slots (normalized to 3+ slots for 100%).
   Availability % = min(active_slots_count / 3.0, 1.0) * 100

NOTE: This is a deterministic rule-based calculation, not an AI/ML prediction model.
"""

from typing import List, Dict, Any
from models import User, MenteeProfile, MentorProfile, UserSkill, LearningInterest, MentorAvailability


def calculate_mentor_recommendations(mentee_user_id: int) -> List[Dict[str, Any]]:
    """
    Calculates weighted match scores for all mentors relative to the specified mentee,
    returning a sorted list of recommendations with full score breakdowns.
    """
    # 1. Resolve MenteeProfile
    mentee_profile = MenteeProfile.query.filter_by(user_id=mentee_user_id).first()
    if not mentee_profile:
        return []

    # 2. Extract mentee's targeted learning skill IDs
    mentee_interests = LearningInterest.query.filter_by(mentee_id=mentee_profile.id).all()
    mentee_skill_ids = {interest.skill_id for interest in mentee_interests}

    # 3. Retrieve all mentor profiles
    mentor_profiles = MentorProfile.query.join(User, MentorProfile.user_id == User.id).all()

    recommendations = []

    for mentor in mentor_profiles:
        # A. Skill Match (50%)
        mentor_user_skills = UserSkill.query.filter_by(user_id=mentor.user_id).all()
        mentor_skill_ids = {us.skill_id for us in mentor_user_skills}

        if mentee_skill_ids:
            matching_skills = mentee_skill_ids.intersection(mentor_skill_ids)
            skill_match_pct = (len(matching_skills) / len(mentee_skill_ids)) * 100.0
        else:
            skill_match_pct = 0.0
        skill_match_score = round(skill_match_pct, 1)

        # B. Experience (20%)
        exp_years = mentor.experience_years or 0
        exp_score = min(max(exp_years, 0) / 10.0, 1.0) * 100.0
        experience_score = round(exp_score, 1)

        # C. Rating (15%)
        if mentor.total_reviews and mentor.total_reviews > 0:
            avg_rating = mentor.average_rating or 0.0
            rating_score = round(min(avg_rating / 5.0, 1.0) * 100.0, 1)
        else:
            # Neutral baseline for newly joined mentors
            rating_score = 50.0

        # D. Availability (15%)
        slot_count = MentorAvailability.query.filter_by(mentor_id=mentor.id).count()
        avail_score = min(slot_count / 3.0, 1.0) * 100.0
        availability_score = round(avail_score, 1)

        # Composite Match Score calculation
        total_score = (
            (0.50 * skill_match_score) +
            (0.20 * experience_score) +
            (0.15 * rating_score) +
            (0.15 * availability_score)
        )
        match_score = round(total_score, 1)

        # Package recommendation structure
        recommendations.append({
            "mentor": {
                "id": mentor.id,
                "user_id": mentor.user_id,
                "name": mentor.user.name if mentor.user else "",
                "bio": mentor.bio or "",
                "experience_years": mentor.experience_years or 0,
                "education": mentor.education or "",
                "current_position": mentor.current_position or "",
                "availability_status": mentor.availability_status or "available",
                "average_rating": mentor.average_rating or 0.0,
                "total_reviews": mentor.total_reviews or 0
            },
            "match_score": match_score,
            "breakdown": {
                "skill_match": skill_match_score,
                "experience": experience_score,
                "rating": rating_score,
                "availability": availability_score
            }
        })

    # Sort descending by match_score, then secondary by experience and rating
    recommendations.sort(
        key=lambda item: (
            item["match_score"],
            item["mentor"]["average_rating"],
            item["mentor"]["experience_years"]
        ),
        reverse=True
    )

    return recommendations
