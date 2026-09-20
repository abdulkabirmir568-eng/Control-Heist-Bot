FEEDBACK_CHANNEL_ID = 0
FEEDBACK_CHANNEL_NAME = "feedback"

COMMUNITY_COLOR = 0xFF6600

POLL_BUTTON_A_LABEL = "Option A"
POLL_BUTTON_B_LABEL = "Option B"

FEEDBACK_MODAL_TITLE = "Heist Control Feedback"
FEEDBACK_SUBJECT_LABEL = "Subject"
FEEDBACK_BODY_LABEL = "Feedback"

EMBEDS: dict[str, tuple[str, str]] = {
    "poll": (
        "# __COMMUNITY POLL__",
        "**** Question:\n{question}\n\n"
        "**** Option A:\n{option_a}\n\n"
        "**** Option B:\n{option_b}\n\n"
        "**** Votes:\nA: {a_count}\nB: {b_count}",
    ),
    "vote_recorded": ("# __VOTE RECORDED__", "**** Selected Option: {option}"),
    "feedback": (
        "# __FEEDBACK RECEIVED__",
        "**** Subject:\n{subject}\n\n"
        "**** Feedback:\n{feedback}\n\n"
        "**** Submitted By:\n{user}",
    ),
    "access_denied": ("# __ACCESS DENIED__", "**** Only leads can use this community command."),
    "announcement": ("# __{title}__", "**** {body}"),
    "announcement_posted": ("# __ANNOUNCEMENT POSTED__", "**** Community announcement posted."),
    "poll_posted": ("# __POLL POSTED__", "**** Community poll posted."),
    "update": ("# __{title}__", "**** {body}"),
    "update_posted": ("# __UPDATE POSTED__", "**** Community update posted."),
}