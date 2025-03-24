from enum import Enum

class TranscribeJobStatus(Enum):
    IN_PROCESS = 0
    COMPLETED = 1
    FAILED = 2