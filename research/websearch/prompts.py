query_writer_instructions="""Your goal is to generate a targeted web search query.
The query will gather information related to a specific topic.

<TOPIC>
{research_topic}
</TOPIC>

<FORMAT>
Format your response as a JSON object with ALL three of these exact keys:
   - "query": The actual search query string
   - "aspect": The specific aspect of the topic being researched
   - "rationale": Brief explanation of why this query is relevant
</FORMAT>

<EXAMPLE>
Example output:
{{
    "query": "machine learning transformer architecture explained",
    "aspect": "technical architecture",
    "rationale": "Understanding the fundamental structure of transformer models"
}}
</EXAMPLE>

Provide your response in JSON format!
Provide your response in JSON format!!!
Provide your response in JSON format!!!!!
Provide your response in JSON format:"""

summarizer_instructions="""
<GOAL>
Generate a high-quality summary of the web search results and keep it concise / related to the user topic.
</GOAL>

<REQUIREMENTS>
When creating a NEW summary:
1. Highlight the most relevant information related to the user topic from the search results
2. Ensure a coherent flow of information

When EXTENDING an existing summary:                                                                                                                 
1. Read the existing summary and new search results carefully.                                                    
2. Compare the new information with the existing summary.                                                         
3. For each piece of new information:                                                                             
    a. If it's related to existing points, integrate it into the relevant paragraph.                               
    b. If it's entirely new but relevant, add a new paragraph with a smooth transition.                            
    c. If it's not relevant to the user topic, skip it.                                                            
4. Ensure all additions are relevant to the user's topic.                                                         
5. Verify that your final output differs from the input summary.                                                                                                                                                            
< /REQUIREMENTS >

< FORMATTING >
- Start directly with the updated summary, without preamble or titles. Do not use XML tags in the output.  
< /FORMATTING >"""

reflection_instructions = """You are an expert research assistant analyzing a summary about {research_topic}.

<GOAL>
1. Identify knowledge gaps or areas that need deeper exploration
2. Generate a follow-up question that would help expand your understanding
3. Focus on technical details, implementation specifics, or emerging trends that weren't fully covered
</GOAL>

<REQUIREMENTS>
Ensure the follow-up question is self-contained and includes necessary context for web search.
</REQUIREMENTS>

<FORMAT>
Format your response as a JSON object with these exact keys:
- knowledge_gap: Describe what information is missing or needs clarification
- follow_up_query: Write a specific question to address this gap
</FORMAT>

<EXAMPLE>
Example output:
{{
    "knowledge_gap": "The summary lacks information about performance metrics and benchmarks",
    "follow_up_query": "What are typical performance benchmarks and metrics used to evaluate [specific technology]?"
}}
</EXAMPLE>

Provide your analysis in JSON format:"""


podcast_script_instructions="""You are an expert podcast script writer. This process started with a user topic: {research_topic}.

You will been given a running summary of the research results.

<GOAL>
1. Convert the running summary into a podcast script that flows naturally in a conversational style.
2. Ensure the script is engaging and informative, suitable for a general audience.
3. Include relevant information from the research results, but keep the script concise and focused on the topic.
4. Use natural language and avoid overly technical jargon.
5. Make the script interesting and engaging for a wide audience.
</GOAL>

<FORMAT>
Format your response as a JSON object with these exact keys:
- podcast_script: The podcast script
</FORMAT>

<EXAMPLE>
Example output:
{{
    "podcast_script": "Welcome to the podcast! Today we're discussing the future of AI and machine learning. We'll explore the latest trends, innovations, and potential impacts on society. Stay tuned for insights from experts and thought leaders in the field."
}}
</EXAMPLE>

Provide your response in JSON format:"""

arxiv_query_writer_instructions="""Your goal is to generate a targeted arXiv search query.
The query will find relevant academic papers and preprints related to a specific research topic.

<TOPIC>
{research_topic}
</TOPIC>

<FORMAT>
Format your response as a JSON object with ALL three of these exact keys:
   - "query": The actual arXiv search query string (use AND, OR, EXACT phrases in quotes as needed)
   - "field": The specific academic field or subfield relevant to this search
   - "rationale": Brief explanation of why this query will find relevant papers
</FORMAT>

<ARXIV TIPS>
- Use quotes for exact phrases: "quantum computing"
- Use AND/OR operators for combinations: "machine learning" AND "computer vision"
- Include relevant author names if specified: au:bengio
- Consider using category filters: cat:cs.AI
- Balance between specificity and breadth for better results
</ARXIV TIPS>

<EXAMPLE>
Example output:
{{
    "query": "\"large language models\" AND \"few-shot learning\"",
    "field": "Machine Learning/Natural Language Processing",
    "rationale": "Targeting papers that explore how large language models perform in few-shot learning scenarios"
}}
</EXAMPLE>

Provide your response in JSON format:"""