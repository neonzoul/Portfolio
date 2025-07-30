### [ ] **Project 4: The "GitHub-to-Discord" Alerter**

**Goal:** Demonstrate a full, event-driven A-to-B integration, combining an API trigger with an API action.

**Functional Requirements:**

-   The application must have a public endpoint (e.g., `/webhook/github`) that can receive webhooks from a GitHub repository.
-   When a "star" event occurs on your repository (a user stars it), the service must parse the webhook payload to extract the username of the person who starred it and the total star count.
-   The service must then immediately post a formatted notification message to a Discord channel via a Discord webhook URL.
-   The Discord message should be a rich embed, formatted like: "**New Star!** ⭐\nYour repo **[Repo Name]** was just starred by **[Username]**. It now has **[X]** stars!".

**Technical Requirements:**

-   Must be built using **FastAPI**.
-   You must create a Pydantic model to validate the incoming GitHub webhook JSON, focusing only on the fields you need (e.g., `action`, `sender['login']`, `repository['stargazers_count']`, `repository['name']`).
-   The POST request to the Discord webhook URL must be made asynchronously using `httpx.AsyncClient`.
-   The Discord webhook URL and any other secrets should be loaded from environment variables, not hardcoded.
-   Must include a `requirements.txt` file (`fastapi`, `uvicorn`, `httpx`, `pydantic`).

---

### [ ] **Project 5: The Scheduled Content Aggregator**

**Goal:** Combine asynchronous scraping with state management by saving data to a persistent database.

**Functional Requirements:**

-   The application must run automatically on a schedule (e.g., once every hour).
-   On each run, it must scrape the titles and URLs of the top 5 articles from at least two different news sources or blogs (e.g., Hacker News and a popular tech blog).
-   The scraped data (title, URL, source, timestamp) must be saved into a PostgreSQL database.
-   The application should avoid inserting duplicate articles. If an article with the same URL already exists, it should be skipped.

**Technical Requirements:**

-   Must be written in Python using `asyncio` and `httpx` for concurrent scraping of the different sources.
-   Scheduling must be implemented using a library like **APScheduler** (`AsyncIOScheduler`).
-   Database interaction must be asynchronous. You must use **SQLModel** (or SQLAlchemy 2.0+) with an async database driver like `asyncpg`.
-   A SQLModel class must be defined for the `Article` table (`id`, `title`, `url`, `source`, `created_at`). The `url` column should have a UNIQUE constraint to prevent duplicates.
-   Database connection details must be loaded from environment variables.
-   Must include a `requirements.txt` file (`httpx`, `apscheduler`, `sqlmodel`, `asyncpg`, `beautifulsoup4`).

---

### [ ] **Project 6: "Micro-Flow": A Two-Node Workflow Engine**

**Goal:** Prove you can architect the core logic of a stateful automation platform like Zapier or n8n.

**Functional Requirements:**

-   The application must provide API endpoints to manage simple, two-step workflows.
-   **Endpoint 1: `POST /workflows`**: Creates a new workflow. It accepts a JSON body specifying an `action_url` and `http_method` (e.g., GET or POST). It saves this to a database and returns a unique `trigger_url` for this workflow (e.g., `https://your-app.com/trigger/{workflow_id}`).
-   **Endpoint 2: `POST /trigger/{workflow_id}`**: This is the webhook trigger. When it receives a POST request, it must look up the corresponding workflow in the database.
-   It must then execute an asynchronous HTTP request to the `action_url` defined for that workflow.
-   The result of the action (success or failure) must be logged to a separate database table.

**Technical Requirements:**

-   Must be built with **FastAPI**.
-   Must use **SQLModel** and an async driver (`asyncpg`) for a PostgreSQL database.
-   You need two database models: `Workflow` (`id`, `action_url`, `http_method`) and `ExecutionLog` (`id`, `workflow_id`, `timestamp`, `status_code`, `success`).
-   The execution of the action HTTP request from the trigger endpoint must be done asynchronously using `httpx`.
-   All API endpoints must be `async def`.
-   Must include a `requirements.txt` file (`fastapi`, `uvicorn`, `sqlmodel`, `asyncpg`, `httpx`).

---

### [ ] **Project 7: The Dynamic Report Generator (Plugin System)**

**Goal:** Demonstrate your ability to build a modular and extensible application using a plugin architecture.

**Functional Requirements:**

-   The application should have a directory named `plugins/`.
-   The application, on startup, must dynamically discover and load any valid "report generator" modules from the `plugins/` directory.
-   It must expose a single API endpoint: `GET /export/{report_format}`.
-   When a user calls this endpoint (e.g., `/export/csv`), the application should find the corresponding plugin (`csv_report.py`) and use it to format a sample dataset into that format.
-   The API should return the formatted data with the correct `Content-Type` header (e.g., `text/csv` for CSV).
-   You must create at least two plugins: one for CSV export (`csv_report.py`) and one for JSON export (`json_report.py`).

**Technical Requirements:**

-   The core application can be built with **FastAPI**.
-   Dynamic plugin discovery and loading must be implemented using Python's `importlib` library.
-   You must define a clear plugin interface. A good way is to create a base class `ReportPlugin` in the main application with an abstract method like `format_data(data)`. Each plugin file must contain a class that inherits from `ReportPlugin` and implements this method.
-   The sample dataset can be a simple hardcoded list of dictionaries in the main application.
-   Must include a `requirements.txt` file (`fastapi`, `uvicorn`).

# Bonus Project.

Of course. Adding projects with AI agent frameworks like LangChain or CrewAI is a perfect next step and a great way to showcase advanced skills. These projects combine your existing focus areas (APIs, async, state) with intelligent, autonomous logic.

Given their complexity, these projects would fit into the higher tiers of your portfolio: **Category 2 (Integrated Systems)** and **Category 3 (Architectural Explorations)**.

Here are four project ideas—two for Software Engineer productivity and two for Marketing—with their detailed requirements.

---

<!-- **For Software Engineer Productivity** -->

#### [] **The GitHub Issue Triage & Labeling Agent**

-   **Category:** 2 (Integrated Systems)
-   **Goal:** Build a system that automatically reads, understands, and categorizes new GitHub issues.
-   **Functional Requirements:**
    -   The system is triggered by a GitHub webhook for new issues.
    -   An AI agent receives the issue's title and body.
    -   The agent's goal is to classify the issue and assign appropriate labels.
    -   The agent must decide if the issue is a `bug`, `feature-request`, or `question`.
    -   Based on its decision, the agent uses the GitHub API to apply the correct label to the issue.
-   **Technical Requirements:**
    -   Use **FastAPI** for the webhook endpoint.
    -   Use **LangChain** or **CrewAI** to create a simple classification agent. You'll provide it with a "tool" that can call the GitHub API to add labels.
    -   This is a great project to practice giving the AI agent a specific, constrained set of choices (the labels).

---

<!-- Marketing Part Project. -->

#### [] **The SEO Content Generation Pipeline Agent**

-   **Category:** 2 (Integrated Systems)
-   **Goal:** Automate the creation of a basic, SEO-optimized blog post from a single keyword.
-   **Functional Requirements:**
    -   The system starts with a single input: a target keyword (e.g., "async python").
    -   **Agent 1 (Researcher):** Takes the keyword and uses a web search tool (e.g., via SerpAPI) to find the top 3-5 ranking articles on that topic. It extracts key points and common themes.
    -   **Agent 2 (Writer):** Takes the research findings from Agent 1 and writes a new, original blog post that covers the key points in a structured way (introduction, main points, conclusion).
    -   The final article is saved as a Markdown file.
-   **Technical Requirements:**
    -   This can be a command-line script or a simple API.
    -   Use **CrewAI** to define a "crew" with two agents (Researcher, Writer), showing you can orchestrate a multi-agent workflow.
    -   The Researcher agent needs a "tool" to perform web searches. You can use a library like `requests-html` or a dedicated search API.
    -   The Writer agent will primarily use the LLM to generate the text based on the context provided by the Researcher.
