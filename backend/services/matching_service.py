"""
Mentor Matching Service.

This service provides a transparent, rule-based mentor recommendation algorithm.
It evaluates compatibility between a mentee's declared learning interests and
available mentors using a weighted multi-criteria scoring formula.

SCORING FORMULA:
Total Match Score = (Skill Match * 0.70) + (Experience * 0.30) + (Rating * 0.10) + (Availability * 0.15)

1. Skill Match (70% weight):
   PRIMARY (when skill-ID rows exist on BOTH sides):
     Percentage of the mentee's targeted learning skills that the mentor possesses.
     Skill Match % = (|Mentee Interests ∩ Mentor Skills| / |Mentee Interests|) * 100

   FALLBACK (when either side has no skill-ID rows):
     Keyword intersection between the mentee's learning_goal text and the
     mentor's current_position + bio text.  Only meaningful technical tokens
     (from the shared skills catalog) contribute; generic words are excluded.
     Scored as: (matched_tech_tokens / mentee_tech_tokens) * 100, capped at 100.
     Returns 0.0 when both texts are empty.

2. Experience (30% weight):
   Evaluates years of professional experience, linearly normalized against a 10-year benchmark.
   Experience % = min(max(experience_years, 0) / 10.0, 1.0) * 100

3. Rating (10% weight):
   Evaluates the mentor's average performance rating (0.0 to 5.0 scale).
   If reviews exist: Rating % = min(average_rating / 5.0, 1.0) * 100
   If no reviews yet: Defaults to a neutral baseline score of 50.0.

4. Availability (15% weight):
   Evaluates active recurring weekly mentoring slots (normalized to 3+ slots for 100%).
   Availability % = min(active_slots_count / 3.0, 1.0) * 100

NOTE: This is a deterministic rule-based calculation, not an AI/ML prediction model.
"""

import re
from typing import List, Dict, Any, Set
from models import User, MenteeProfile, MentorProfile, UserSkill, LearningInterest, MentorAvailability, Skill

# ---------------------------------------------------------------------------
# Generic stop-words that must not contribute to technical matching on their
# own.  Words like "development" or "learning" are too broad and appear in
# almost every mentor bio regardless of specialisation.
# ---------------------------------------------------------------------------
_STOP_WORDS: Set[str] = {
    # articles / prepositions / conjunctions
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "it", "its", "i", "my", "me",
    "we", "us", "you", "he", "she", "they", "be", "am", "are", "was",
    "were", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall", "can",
    # generic tech / learning words that appear universally
    "learn", "learning", "teach", "teaching", "guide", "guides", "develop",
    "developing", "development", "code", "coding", "program", "programming",
    "project", "projects", "skill", "skills", "build", "building",
    "application", "applications", "technology", "technologies", "tech",
    "software", "engineer", "engineering", "developer", "developers",
    "student", "students", "mentor", "mentoring", "understand", "help",
    "want", "use", "using", "work", "working", "also", "their", "this",
    "that", "these", "those", "how", "about", "strong", "industry",
    "relevant", "tools", "stack", "web", "full",
}

# Multi-word canonical technology aliases: each tuple is (canonical_token, [aliases…]).
# All matching is done on lowercased text so aliases here are already lowercase.
_TECH_ALIASES = [
    ("javascript",  ["javascript", "js"]),
    ("typescript",  ["typescript", "ts"]),
    ("nodejs",      ["node.js", "nodejs", "node"]),
    ("react",       ["react", "reactjs", "react.js"]),
    ("flask",       ["flask"]),
    ("html",        ["html", "html5"]),
    ("css",         ["css", "css3"]),
    ("htmlcss",     ["html & css", "html&css", "html css"]),
    ("python",      ["python"]),
    ("java",        ["java"]),
    ("cplusplus",   ["c++", "cpp"]),
    ("golang",      ["golang", "go"]),
    ("sql",         ["sql", "mysql", "postgresql", "sqlite", "database",
                     "databases", "db"]),
    ("ml",          ["machine learning", "ml"]),
    ("dl",          ["deep learning", "dl"]),
    ("dataanalysis",["data analysis", "data analytics"]),
    ("docker",      ["docker", "containers", "containerization"]),
    ("aws",         ["aws", "amazon web services", "cloud"]),
    ("cicd",        ["ci/cd", "cicd", "devops", "pipelines"]),
    ("architecture",["system architecture", "architecture"]),
    ("fullstack",   ["full-stack", "full stack", "fullstack",
                     "frontend", "front-end", "front end",
                     "backend", "back-end", "back end"]),
]


def _apply_multi_word_aliases(text: str) -> str:
    """
    Replace multi-word and symbol-containing alias phrases with a single
    canonical token so that later single-word tokenisation captures them.
    Applied before tokenisation, longest-phrase-first to avoid partial hits.
    """
    # Sort by phrase length descending so longer phrases match first.
    phrases = []
    for canonical, aliases in _TECH_ALIASES:
        for alias in aliases:
            if " " in alias or "/" in alias or "." in alias or "&" in alias or "+" in alias:
                phrases.append((alias, canonical))
    phrases.sort(key=lambda x: len(x[0]), reverse=True)

    for phrase, canonical in phrases:
        text = text.replace(phrase, " " + canonical + " ")
    return text


def _tech_tokens(text: str) -> Set[str]:
    """
    Extract the set of meaningful technical tokens from a text string.

    Steps:
    1. Lower-case.
    2. Apply multi-word alias substitution.
    3. Tokenise on non-alphanumeric boundaries.
    4. Map single-word aliases to their canonical token.
    5. Discard stop-words and tokens shorter than 2 characters.
    6. Return the resulting set of canonical technical tokens.
    """
    if not text or not text.strip():
        return set()

    text = text.lower()
    text = _apply_multi_word_aliases(text)

    # Build single-word alias lookup: alias_word -> canonical
    single_word_map = {}
    for canonical, aliases in _TECH_ALIASES:
        for alias in aliases:
            # Only single-word aliases at this stage
            if " " not in alias and "/" not in alias and "." not in alias \
                    and "&" not in alias and "+" not in alias:
                single_word_map[alias] = canonical

    raw_tokens = re.split(r"[^a-z0-9]+", text)
    result = set()
    for tok in raw_tokens:
        tok = tok.strip()
        if len(tok) < 2:
            continue
        # Map through alias table first
        canonical = single_word_map.get(tok, tok)
        if canonical not in _STOP_WORDS:
            result.add(canonical)
    return result


def _text_skill_match_pct(mentee_goal: str, mentor_position: str, mentor_bio: str) -> float:
    """
    Compute a text-based skill-match percentage when normalised skill-ID rows
    are unavailable on one or both sides.

    Scores how well the mentor's position + bio covers the technical tokens
    expressed in the mentee's learning goal.

    Returns a float in [0.0, 100.0].  Returns 0.0 when the mentee goal is
    empty (cannot determine intent) rather than returning an inflated value.
    """
    mentee_tokens = _tech_tokens(mentee_goal or "")
    if not mentee_tokens:
        # No parseable intent from the mentee — cannot determine match.
        return 0.0

    mentor_text = " ".join([mentor_position or "", mentor_bio or ""])
    mentor_tokens = _tech_tokens(mentor_text)

    if not mentor_tokens:
        return 0.0

    matched = mentee_tokens.intersection(mentor_tokens)
    return min((len(matched) / len(mentee_tokens)) * 100.0, 100.0)


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
        # A. Skill Match (50%) — primary: skill-ID intersection; fallback: text match
        mentor_user_skills = UserSkill.query.filter_by(user_id=mentor.user_id).all()
        mentor_skill_ids = {us.skill_id for us in mentor_user_skills}

        if mentee_skill_ids and mentor_skill_ids:
            # PRIMARY path: both sides have normalised skill-ID rows.
            matching_skills = mentee_skill_ids.intersection(mentor_skill_ids)
            skill_match_pct = (len(matching_skills) / len(mentee_skill_ids)) * 100.0
        else:
            # FALLBACK path: at least one side has no skill-ID rows.
            # Use text from mentee's learning_goal vs mentor's position + bio.
            skill_match_pct = _text_skill_match_pct(
                mentee_profile.learning_goal,
                mentor.current_position,
                mentor.bio,
            )
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
                "email": mentor.user.email if mentor.user else "",
                "profile_picture": mentor.user.profile_picture if mentor.user else None,
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
