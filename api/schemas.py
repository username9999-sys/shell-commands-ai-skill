from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SafetyLevel(str, Enum):
    SAFE = "safe"
    ALLOW_RISKY = "allow-risky-examples"


class CommandOption(BaseModel):
    flag: str
    desc: str
    examples: List[str] = []


class CommandExample(BaseModel):
    code: str
    explain: str
    destructive: bool = False


class CommandBase(BaseModel):
    name: str
    category: str
    one_line: str
    usage: str
    options: List[CommandOption] = []
    examples: List[CommandExample] = []
    risk_level: RiskLevel = RiskLevel.LOW
    safety: str
    related_commands: List[str] = []
    source: str
    source_version: str = ""
    fetched_at: str = ""


class Command(CommandBase):
    id: str = Field(alias="_id")


class CommandCreate(CommandBase):
    pass


class CommandUpdate(BaseModel):
    one_line: Optional[str] = None
    usage: Optional[str] = None
    options: Optional[List[CommandOption]] = None
    examples: Optional[List[CommandExample]] = None
    risk_level: Optional[RiskLevel] = None
    safety: Optional[str] = None
    related_commands: Optional[List[str]] = None


class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    semantic: bool = True


class ExplainRequest(BaseModel):
    command: str
    context: Optional[str] = None
    os: Optional[str] = None
    shell: Optional[str] = None
    safety: SafetyLevel = SafetyLevel.SAFE


class ListCommandsRequest(BaseModel):
    category: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort: str = Field(default="name", pattern="^(name|category|risk_level)$")
    order: str = Field(default="asc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    items: List[Command]
    total: int
    limit: int
    offset: int
    has_more: bool


class CategorySummary(BaseModel):
    category: str
    count: int


class SummaryResponse(BaseModel):
    total_commands: int
    categories: List[CategorySummary]
    generated_at: str


class HealthResponse(BaseModel):
    status: str
    version: str
    commands_indexed: int
    index_updated_at: str