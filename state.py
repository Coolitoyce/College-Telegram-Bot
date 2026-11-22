import database
from config import UserState, user_states


#=============================================================================
# Persistent navigation state helpers

async def get_navigation_state(user_id: int) -> UserState:
    """Returns an in-memory state, loading persisted navigation if it is new."""
    if user_id in user_states:
        return user_states[user_id]

    year, semester, department, course_id = await database.get_user_navigation(user_id)

    # Temporary fields keep their dataclass defaults. This helper intentionally
    # never restores awaiting, sent_files, pending_message, or bulk-upload values.
    state = UserState(
        year=year,
        semester=semester,
        department=department,
        course_id=course_id
    )
    user_states[user_id] = state
    return state


async def save_navigation_state(user_id: int, state: UserState):
    """Caches a state and saves only its four navigation fields in SQLite."""
    user_states[user_id] = state

    await database.save_user_navigation(
        user_id,
        year=state.year,
        semester=state.semester,
        department=state.department,
        course_id=state.course_id
    )


async def clear_navigation_state(user_id: int):
    """Clears saved and cached navigation, leaving temporary workflow fields alone."""
    state = await get_navigation_state(user_id)

    # A full reset should clear only the values that describe menu navigation.
    state.year = None
    state.semester = None
    state.department = None
    state.course_id = None

    await database.clear_user_navigation(user_id)
