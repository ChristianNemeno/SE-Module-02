# app/models/cv_detector.py
from typing import Protocol, TypedDict


class CVFlags(TypedDict):
    """GO3 behavioral flags from the reading video — finger pointing + loss of place."""

    finger_pointing: bool
    loss_of_place: bool


class CVDetectorProtocol(Protocol):
    """Interface for the CV detector — pipeline depends on this, not the concrete class."""

    def detect(self, video_path: str) -> CVFlags: ...
