### [ ] **Project 1: The Concurrent Asset Downloader**

**Goal:** Prove mastery of fundamental asynchronous I/O for network-bound tasks.

**Functional Requirements:**

-   The application must be a command-line tool.
-   It must accept one command-line argument: the path to a text file (`--urls-file urls.txt`).
-   The text file will contain one URL per line. The tool must read all URLs from this file.
-   The tool must create a directory named `downloads/` if it doesn't already exist.
-   It must download the content from every URL and save each file into the `downloads/` directory. The filename should be derived from the last part of the URL (e.g., `https://example.com/images/photo.jpg` becomes `photo.jpg`).
-   The tool must print progress to the console (e.g., "Downloading `photo.jpg`...", "Finished `photo.jpg`.").
-   After all downloads are complete, it must print a summary: "Finished downloading X files."

**Technical Requirements:**

-   Must be written in Python.
-   Must use the `asyncio` library to manage concurrency.
-   Must use `httpx.AsyncClient` for making the HTTP requests.
-   The core download logic for all URLs must be run concurrently using a tool like `asyncio.gather`.
-   Must include a `requirements.txt` file listing all dependencies (`httpx`).

---

### [ ] **Project 2: The Live Dashboard API Backend**

**Goal:** Demonstrate handling of persistent, real-time, asynchronous connections.

**Functional Requirements:**

-   The application must be a web server.
-   It must expose a WebSocket endpoint at `/ws/cpu-updates`.
-   When a client connects to the WebSocket, the server must start sending simulated CPU usage data every second.
-   The data sent to the client must be in JSON format, like: `{"timestamp": "YYYY-MM-DDTHH:MM:SS", "cpu_usage": 75.4}`. The `cpu_usage` should be a random float between 20.0 and 90.0.
-   The server must handle multiple clients connected simultaneously, each receiving the same stream of updates.
-   The server should gracefully handle client disconnects without crashing.

**Technical Requirements:**

-   Must be built using the **FastAPI** framework.
-   The WebSocket logic must be implemented using `async def` endpoints.
-   The periodic data push (every second) must be managed with an `asyncio.sleep(1)` inside an asynchronous loop.
-   You must provide a very simple `index.html` file with minimal JavaScript that can connect to the WebSocket and display the incoming messages on the page, proving that the backend works.
-   Must include a `requirements.txt` file (`fastapi`, `uvicorn`, `websockets`).

---

### [ ] **Project 3: The Universal Webhook Ingestion Service**

**Goal:** Prove you can build a stable, event-driven entry point for an automation workflow.

**Functional Requirements:**

-   The application must be a web server that listens for incoming webhooks.
-   It must have a single endpoint at `/webhook` that only accepts `POST` requests.
-   The endpoint must be able to accept _any_ valid JSON body.
-   Upon receiving a `POST` request, the service must log the following to the console or a log file:
    -   The timestamp of when the webhook was received.
    -   The headers of the incoming request (specifically `User-Agent` and `Content-Type`).
    -   The full, prettified JSON body of the webhook.
-   The endpoint should immediately return a `200 OK` status with a simple JSON response: `{"status": "received"}`.

**Technical Requirements:**

-   Must be built using the **FastAPI** framework.
-   The endpoint must be an `async def` function.
-   To handle an arbitrary JSON body, you can accept the raw `Request` object from FastAPI and call `await request.json()`.
-   Logging should be implemented using Python's standard `logging` module.
-   Must include a `requirements.txt` file (`fastapi`, `uvicorn`).

### Bonus

Can try to master Asyncio maybe with Make faster API Calls like.
https://www.youtube.com/watch?v=nFn4_nA_yk8&list=PLrh_Jn2lrdcQ96gLtjGC9G4HVv9ierQDT&index=3&ab_channel=PatrickCollins

Or Automation, Productivity things.
