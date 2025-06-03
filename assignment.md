SkillCat Work Sample
“Ask the Web” – Streamlit Q & A with Citations
(Full-Stack Python / Junior)

-------------------------------------------------------------------------------------------------------------------------------
Table of Contents
A. Overview 1
B. Core Task 1
Functional requirements 2
Non-functional requirements 2
C. Stretch Task (Optional) 2
D. Deliverables 3
E. Evaluation Rubric 3
F. Guidelines & Policies 4

-------------------------------------------------------------------------------------------------------------------------------


A. Overview
This miniature project lets you show how you can turn a user prompt into a working, end-to-end product:
Scrape & clean web data
Use an LLM to answer a question and add inline citations
Wrap the flow in a simple Streamlit UI
Ship code that is readable, tested, and dockerised
Plan to spend ≈ 3 focused hours on the Core Task. A small Stretch section is optional (+2 h max).

B. Core Task
Build a Streamlit app called “Ask the Web” that lets a user type any question and receive:
 • an answer in plain English with numbered citations, and
 • a list of source-page titles (each citation links to the page).
Functional requirements
Step
What must happen
1
Search – Query a public web search API (any free option such as DuckDuckGo Search, SerpAPI free tier, Brave Search, etc.) and fetch the top ≤ 5 organic results.
2
Scrape – Download & extract main text from each result (BeautifulSoup, Newspaper3k, Readability-lxml—your choice).
3
Answer – Pass the user question and the scraped texts to an LLM (OpenAI, Gemini, Mistral, Ollama-local—any model you can legally access).
4
Citations – Instruct the LLM to cite sources as [1] … [n]; return a markdown answer plus a “Sources” section listing title + URL for each id.
5
UI – Streamlit page with: single text input, “Ask” button, answer panel, and an expandable “Debug” section that shows raw JSON of search results.


Non-functional requirements
Environment variables for all API keys; include a .env.example.
Python 3.10+, requirements.txt (or pyproject.toml).
Tests – at least one unit test for the text-extraction helper or the citation-parsing logic (pytest).
Docker – docker build . && docker run -p 8501:8501 ask-web must start the app.
README ≤ 1 page – setup, how it works, prompts used, known limits.

C. Stretch Task (Optional)
Pick one if you have extra time (max +2 h):
Telemetry sidebar – live display of total tokens & end-to-end latency per query.
Answer quality check – after replying, call a second LLM that critiques whether each citation really supports the sentence it is attached to; display a pass/fail badge.

D. Deliverables
Item
Where & format
1
GitHub repo (public or private invite) containing code, tests, Dockerfile.
2
README.md – setup (≤ 5 commands), architecture diagram (ASCII or image), LLM prompt(s) with one-sentence rationale.
3
Loom video ≤ 2 minutes: demo the app & highlight code structure.
4
Your résumé in the same repo or the Drive folder you share.

Email the link to salome@skillcatapp.com with subject “Ask the Web Work Sample – <Your Name>” within 7 days (ask early if you need more time).

E. Evaluation Rubric
Scorecard Area
Weight
What earns 5/5
Problem-Solving & Communication
20 %
Clear README & Loom; sensible assumptions; graceful error handling.
Python Proficiency
20 %
Idiomatic code, typing, docstrings, green pytest.
Backend Development
15 %
Clean separation of search, scrape, LLM modules; retries & timeouts.
Frontend Development
15 %
Streamlit layout is tidy; state handled correctly; no blocking calls on UI thread.
AI Fundamentals
10 %
Prompt shows awareness of context length & hallucination risks.
LLMs & Agents
20 %
Citations reliably map to sources; optional critique agent (stretch) works.
Prompt Engineering
10 %
Prompt iterations explained; citations enforced via prompt logic.
Cloud / CI
5 %
Docker image runs; optional GH Actions passes on push.


F. Guidelines & Policies
You may use any open-source library and any free search/LLM tier.
Do not commit secrets—use env vars.
Cite all 3rd-party code in the README.
All work remains confidential and will be used for hiring evaluation only.

Good luck & have fun building Ask the Web!