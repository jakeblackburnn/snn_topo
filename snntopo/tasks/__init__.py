"""Task registry. To add a task: subclass contracts.Task in a new module and add one
line below. Matched tasks set bio_match to a DATASETS key and use that dataset's
condition names as action_names; generic tasks set bio_match = None."""
from ..contracts import Task
from .dms import DMS
from .nback import NBack
from .steinmetz_2afc import Steinmetz2AFC

TASKS: dict[str, Task] = {
    "steinmetz_2afc": Steinmetz2AFC(),
    "nback": NBack(),
    "dms": DMS(),
}
