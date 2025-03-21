import os
from dataclasses import dataclass, fields, field
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from dataclasses import dataclass
from langchain_openai import ChatOpenAI

from enum import Enum

class SearchAPI(Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"

@dataclass(kw_only=True)
class Configuration:
    """The configurable fields for the research assistant."""
    max_web_research_loops: int = field(default_factory=lambda: int(os.environ.get("MAX_WEB_RESEARCH_LOOPS") or "3"))

    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY")

    search_api: SearchAPI = SearchAPI(os.environ.get("SEARCH_API", SearchAPI.DUCKDUCKGO.value))  # Default to DUCKDUCKGO
    fetch_full_page: bool = os.environ.get("FETCH_FULL_PAGE", "False").lower() in ("true", "1", "t")
    

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})