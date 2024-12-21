from typing import Literal

Status = Literal["preprocessing", "running", "postprocessing", "finished", "error"]

FileType = Literal["artifact", "output", "log"]
