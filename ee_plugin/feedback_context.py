import threading

_local = threading.local()


def set_feedback(feedback):
    _local.feedback = feedback


def get_feedback():
    return getattr(_local, "feedback", None)
