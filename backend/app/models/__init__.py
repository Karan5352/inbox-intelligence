"""ORM models. Importing this package registers every mapper with the Base."""

from app.models.automation import Automation
from app.models.correction import Correction
from app.models.email import Email
from app.models.metric import Metric

__all__ = ["Email", "Correction", "Automation", "Metric"]
