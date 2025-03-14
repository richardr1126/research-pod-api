import operator
from dataclasses import dataclass, field
from typing_extensions import TypedDict, Annotated

def dict_update(d1, d2):
    """Custom merge function for dictionaries that handles the web search results."""
    if not d1:
        return d2
    if not d2:
        return d1
    
    # For search results, we want to append to the 'results' list
    if 'results' in d1 and 'results' in d2:
        merged = d1.copy()
        merged['results'] = d1['results'] + d2['results']
        return merged
    
    # Default fallback: update d1 with d2
    merged = d1.copy()
    merged.update(d2)
    return merged

@dataclass(kw_only=True)
class SummaryState:
    research_topic: str = field(default=None) # Report topic     
    search_query: str = field(default=None) # Search query
    web_research_results: Annotated[list, operator.add] = field(default_factory=list) 
    sources_gathered: Annotated[dict, dict_update] = field(default_factory=dict)
    research_loop_count: int = field(default=0) # Research loop count
    running_summary: str = field(default=None) # Final report

@dataclass(kw_only=True)
class SummaryStateInput:
    research_topic: str = field(default=None) # Report topic     

@dataclass(kw_only=True)
class SummaryStateOutput:
    sources_gathered: Annotated[dict, dict_update] = field(default_factory=dict)