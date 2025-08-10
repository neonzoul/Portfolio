### **Assignment: User API Key Management**

**Objective:**
Build the API endpoints required for a logged-in user to generate, view, and revoke their own API keys. This is a critical feature for any automation platform, as it allows external services and CLIs to interact securely with a user's account.

---

### **1. Data Model & Database**

First, you need a way to store the API keys in your PostgreSQL database.

-   **Task:** Define a new `ApiKey` table using SQLModel. It should have the following fields:
    -   `id`: The primary key (integer or UUID).
    -   `key_prefix`: A short, non-secret part of the key that is safe to display (e.g., `aosk_...`). This helps users identify their keys.
    -   `hashed_key`: The securely hashed version of the full API key. **Never store the full key in the database.**
    -   `created_at`: A timestamp for when the key was created.
    -   `user_id`: A foreign key that links this key to the `id` in your `User` table.
-   **Task:** Update your `User` model to include the one-to-many relationship to the `ApiKey` model.
-   **Task:** Use `alembic` to generate a new migration file and apply it to your database to create the table.

---

### **2. Core Logic & Security**

This is where you'll use `passlib`.

-   **Task:** In your `app/core/security.py` file, create two new helper functions:
    1.  `generate_api_key() -> (str, str)`: This function should generate a new, secure random key string. It should return both the plain text key (to show to the user once) and its corresponding prefix.
    2.  `hash_api_key(plain_key: str) -> str`: This function takes the plain text key and returns a secure hash of it using `passlib`.

---

### **3. API Endpoints**

Now, build the user-facing endpoints. All of these endpoints must be **protected** and require a valid JWT from a logged-in user.

**A. Create a New API Key**

-   **Endpoint:** `POST /users/me/apikeys`
-   **Action:**
    1.  Get the current user from the JWT dependency.
    2.  Call your `generate_api_key()` helper to create a new key and prefix.
    3.  Call your `hash_api_key()` helper to hash the new key.
    4.  Create a new `ApiKey` instance in the database, storing the `key_prefix`, `hashed_key`, and the current `user_id`.
-   **Response:** Return the `id`, `key_prefix`, `created_at`, and the **full, plain text API key**. This is the **only time** the user will ever see the full key.

**B. List Existing API Keys**

-   **Endpoint:** `GET /users/me/apikeys`
-   **Action:**
    1.  Get the current user from the JWT dependency.
    2.  Query the database for all `ApiKey` records associated with that user's ID.
-   **Response:** Return a list of API keys, but **only include the safe metadata**: `id`, `key_prefix`, and `created_at`.

**C. Revoke (Delete) an API Key**

-   **Endpoint:** `DELETE /users/me/apikeys/{key_id}`
-   **Action:**
    1.  Get the current user from the JWT dependency.
    2.  Find the `ApiKey` in the database by its `key_id`.
    3.  **Perform an authorization check:** Verify that the `user_id` on the key matches the ID of the current user. If it does not, raise an `HTTPException` with a `403 Forbidden` status.
    4.  If the check passes, delete the key from the database.
-   **Response:** On success, return a `204 No Content` status code.

---

### **Final Presentation Goal (Definition of Done)**

Your assignment is complete when you can demonstrate the full lifecycle through the FastAPI `/docs` interface:

1.  **Register** a new user.
2.  **Login** as that user to get a JWT access token.
3.  **Authorize** your session in the `/docs` by pasting the JWT.
4.  **Execute** the `POST /users/me/apikeys` endpoint and see the new, full API key returned in the response.
5.  **Execute** the `GET /users/me/apikeys` endpoint and see a list containing just the metadata (prefix, ID) of the key you just created.
6.  **Execute** the `DELETE /users/me/apikeys/{key_id}` endpoint to successfully revoke the key.
7.  **Verify** the key is gone by running the `GET` endpoint again, which should now return an empty list.
