from typing import Literal

from pydantic import BaseModel, ConfigDict


class RiskNotification(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  level: Literal["high", "medium", "low"]
  message: str
