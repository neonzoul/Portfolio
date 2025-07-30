### [ ] **Project 8: The Resilient API Client Library**

**Goal:** Demonstrate that you think defensively about system stability and can build fault-tolerant components.

**Functional Requirements:**

-   Create a reusable Python class, `ResilientClient`, that can be used to make robust HTTP requests.
-   The class constructor should accept configuration for retries, such as `max_retries` (e.g., 3) and `initial_delay` (e.g., 1 second).
-   It must have an `async def request()` method that works similarly to `httpx.AsyncClient.request()`.
-   If an API call fails (e.g., receives a 5xx status code or a timeout), the `request()` method must automatically retry the call.
-   The delay between retries must increase. You must implement an "exponential backoff" strategy (e.g., delay is `initial_delay * 2 ** (retry_attempt - 1)`).
-   If the request fails after all retry attempts, it should raise a final exception.
-   You must include a simple example script that demonstrates the client trying to connect to an unreliable (mock) endpoint and successfully getting a response after a few retries.

**Technical Requirements:**

-   The library must be built using `asyncio` and wrap the `httpx.AsyncClient`.
-   The delay between retries must be implemented using `asyncio.sleep()`.
-   The logic for exponential backoff must be clearly implemented and commented.
-   To simulate an unreliable API for your example, you can create a simple FastAPI app with an endpoint that fails the first two times it's called before succeeding on the third attempt.
-   Must include a `requirements.txt` file (`httpx`).

---

### [ ] **Project 9: The Simple API Gateway**

**Goal:** Prove your understanding of microservice architecture and how to manage and simplify a system's entry point.

**Functional Requirements:**

-   The application must be a single FastAPI server that acts as a reverse proxy or "gateway."
-   It must listen on a primary port (e.g., 8000).
-   It must intelligently route incoming requests to two separate, mock backend microservices running on different ports (e.g., 9001 and 9002).
-   Any request to `/users/{path:path}` should be forwarded to the "User Service" on port 9001.
-   Any request to `/orders/{path:path}` should be forwarded to the "Order Service" on port 9002.
-   The gateway must correctly forward the HTTP method, headers, query parameters, and body of the original request.
-   The response from the microservice (status code, headers, and body) must be returned transparently to the original client.

**Technical Requirements:**

-   The gateway must be built with **FastAPI**.
-   The request forwarding logic must use `httpx.AsyncClient` to make the downstream API calls asynchronously.
-   You must create two other very simple FastAPI applications to act as the mock "User Service" and "Order Service." Each should have a few dummy endpoints that return simple JSON responses (e.g., a `GET /users/123` in the User Service returns `{"user_id": 123, "name": "John Doe"}`).
-   You will need a `docker-compose.yml` file or a simple script to run all three services (Gateway, User Service, Order Service) at the same time for demonstration.
-   Must include a `requirements.txt` file (`fastapi`, `uvicorn`, `httpx`).

---

### [ ] **Project 10: The Background Task Processor**

**Goal:** Demonstrate your understanding of how to build responsive, non-blocking applications by offloading long-running tasks.

**Functional Requirements:**

-   The application must provide a web API with at least two endpoints.
-   **Endpoint 1: `POST /generate-report`**: This endpoint simulates a long-running task. It should **not** block. It must immediately return a `202 Accepted` status code with a JSON body containing a `job_id` (e.g., `{"job_id": "some-unique-id"}`).
-   This endpoint must push the "report generation" task into a background worker queue. The task itself can be simple: wait for 15 seconds, then write the current time to a text file named `{job_id}.txt`.
-   **Endpoint 2: `GET /reports/{job_id}/status`**: This endpoint allows a client to check the status of a job. It should return a JSON response indicating whether the job is "pending," "in-progress," or "complete."

**Technical Requirements:**

-   The API must be built with **FastAPI**.
-   You must integrate a task queue library like **Celery** or **Redis Queue (RQ)**. Celery with a Redis broker is an industry standard and an excellent skill to showcase.
-   You will need to run at least two separate processes: the FastAPI web server and the Celery background worker.
-   The 15-second wait in the background task should be simulated with `time.sleep(15)`. This is a rare case where using a blocking call is okay, as it's in a separate worker process and is meant to simulate a CPU-bound or long I/O task.
-   A `docker-compose.yml` file is the best way to manage and run the multiple services required (FastAPI app, Celery worker, Redis broker).
-   Must include a `requirements.txt` file (`fastapi`, `uvicorn`, `celery`, `redis`).

# Bonus Projects.

<!-- For Software Engineer Productivity -->

#### []**The Automated Code Review Agent**

-   **Category:** 3 (Architectural Explorations)
-   **Goal:** Create an agent that acts as an automated peer reviewer for pull requests.
-   **Functional Requirements:**
    -   The system must be triggered by a GitHub webhook when a new pull request is opened.
    -   An AI agent (using CrewAI) receives the code changes from the pull request.
    -   The agent must have a specific goal: "Analyze the provided code for potential bugs, style guide violations (e.g., PEP 8), and opportunities for refactoring."
    -   The agent must have access to a "tool" that can read files from a GitHub repository.
    -   After analysis, the agent must use the GitHub API to post its findings as a formatted comment on the pull request.
-   **Technical Requirements:**
    -   Use **FastAPI** to receive the GitHub webhook.
    -   Use **CrewAI** or **LangChain** to define the agent, its role ("Expert Code Reviewer"), and its goal.
    -   The agent's "tool" for reading files will be a Python function that uses `httpx` to make authenticated calls to the GitHub API.
    -   The entire process, from receiving the webhook to the agent's analysis, should run asynchronously.

<!-- Community Driven CRM Project. -->

### [] **Project: The Community CRM & Insights Agent**

-   **Goal:** Create an AI agent that monitors a Discord community, automatically manages new members, and provides intelligent insights, acting as a lightweight, automated Community Manager.

-   **Functional Requirements:**
-   The system must be a Discord bot that can be invited to a server.
-   **New Member Onboarding:** When a new member joins the server, the agent must:
    1.  Send a personalized welcome message to a specific `#introductions` channel, tagging the new user.
    2.  Create a new "lead" or "community member" record in a simple CRM database (PostgreSQL table).
-   **Lead/Interest Identification:** The agent must listen for messages in specific channels (e.g., `#general-chat`, `#product-questions`).
    -   If a message contains keywords indicating a strong interest in a product or service (e.g., "how do I buy," "pricing," "sign up"), the agent should flag the corresponding member's record in the CRM as a "Hot Lead."
-   **Community Insights:** The agent must have a command that a human admin can trigger (e.g., `!summarize-day`).
    -   When triggered, the agent will read the last 24 hours of messages from a specified channel, use an LLM to generate a concise summary of the main topics and overall sentiment (positive/neutral/negative), and post this summary in a private `#admin-reports` channel.

**Technical Requirements:**

-   [cite_start]The bot must be built using Python with the `discord.py` library, which is fully asynchronous. [cite: 2]
-   [cite_start]Use **CrewAI** or **LangChain** to define the agent's logic, especially for the `!summarize-day` command, which requires understanding and summarizing conversation context. [cite: 1]
-   [cite_start]The CRM backend must be a **PostgreSQL** database managed with **SQLModel** and an async driver like `asyncpg`. [cite: 5, 6, 7]
-   [cite_start]Interaction with the database (creating members, updating lead status) must be done asynchronously within the bot's event handlers. [cite: 2, 5]
-   All secrets (Discord Bot Token, database URL) must be loaded from environment variables.
-   Must include a `requirements.txt` file (`discord.py`, `crewai` or `langchain`, `sqlmodel`, `asyncpg`, `python-dotenv`).
