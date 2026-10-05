"""CV stage ports. Implementations are deferred until model/dataset approval."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import BinaryIO, Protocol

from .contracts import CVResult, ProcessingRequest


@dataclass(frozen=True)
class VideoFrame:
    timestamp_ms: int
    image: object


@dataclass(frozen=True)
class Detection:
    frame_timestamp_ms: int
    box_xyxy: tuple[float, float, float, float]
    confidence: float


@dataclass(frozen=True)
class Track:
    track_ref: str
    detections: tuple[Detection, ...]


class VideoProcessor(Protocol):
    def process(self, request: ProcessingRequest, video: BinaryIO) -> CVResult: ...


class FrameExtractor(Protocol):
    def extract(self, video: BinaryIO, *, target_fps: float) -> Iterable[VideoFrame]: ...


class PersonDetector(Protocol):
    def detect(self, frames: Iterable[VideoFrame]) -> Iterable[Detection]: ...


class Tracker(Protocol):
    def track(self, detections: Iterable[Detection]) -> Sequence[Track]: ...


class FaceLandmarkAnalyzer(Protocol):
    def analyze(self, tracks: Sequence[Track]) -> Iterable[dict[str, object]]: ...


class ObservableFeatureExtractor(Protocol):
    def extract(self, landmarks: Iterable[dict[str, object]]) -> Iterable[dict[str, object]]: ...


class TemporalAnalyzer(Protocol):
    def aggregate(self, observations: Iterable[dict[str, object]]) -> CVResult: ...
