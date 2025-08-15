### Project: Basic Inventory Management API

**🎯 Core Objective:** Build a simple, reliable API to track products and their stock levels. The main goal is to correctly manage the **state** (the quantity) of each product as it changes over time.

---

### ✅ Project Expectations

Your final submission should be a working API application that meets these requirements:

1.  **Product Model:** A product in your system must have:
    * A unique **SKU** (Stock Keeping Unit), e.g., `TSHIRT-RED-L`. This is its primary identifier.
    * A **Name**, e.g., "Red T-Shirt (Large)".
    * A **Description** (optional).
    * An integer **Quantity** representing the current stock level.

2.  **API Endpoints:** Your API must have the following endpoints:
    * `POST /products`: Creates a new product. Requires a SKU, name, and initial quantity.
    * `GET /products`: Returns a list of all products.
    * `GET /products/{sku}`: Returns the details for a single product, identified by its SKU.
    * `PATCH /products/{sku}/add`: Adds stock to a product. The request body should specify the amount to add (e.g., `{ "amount": 50 }`).
    * `PATCH /products/{sku}/remove`: Removes stock from a product. The request body should specify the amount to remove (e.g., `{ "amount": 10 }`). This endpoint **must fail** if the requested amount is greater than the available quantity.

---

### 🧠 How Deep You Should Understand

This project is about fundamentals. Focus on understanding these concepts deeply, not just making them work.

#### **1. RESTful API Design (Focus Area)**

* **What it is:** A standard way of designing APIs so they are predictable and easy to use.
* **How Deep:** You should be able to answer:
    * Why are we using `POST` for creating and `GET` for reading? Understand the purpose of **HTTP verbs**.
    * Why are we using a URL like `/products/{sku}` to identify a specific item? Understand the concept of a **resource-based URL**.
    * What **HTTP status codes** should you return? Know the difference between `200 OK`, `201 Created`, `404 Not Found`, and `400 Bad Request`. For example, trying to remove too much stock should return a `400`.

#### **2. Data Modeling (Focus Area)**

* **What it is:** Designing the database table(s) to store your information efficiently.
* **How Deep:** You should understand:
    * **Primary Keys vs. Unique Constraints:** Why is the `sku` a good candidate for a unique identifier that users interact with, even if you have a separate auto-incrementing `id` as the primary key?
    * **Data Types:** Why is `quantity` an integer? What are the implications?
    * **Database Constraints:** You should add a `CHECK` constraint in your database schema to ensure the `quantity` column can **never be negative**. This is a critical safety net.

---

### ⭐ State Management: The Most Important Focus

This is the heart of the project.

#### **What is "State"?**

In this project, the **state** is simply the value in the `quantity` column for a given product. State management is the process of ensuring this value is always accurate, especially when multiple things are trying to change it at once.

#### **The Core Problem: Race Conditions**

Imagine you have **1** "Blue T-Shirt" left in stock.
Two customers, A and B, try to buy it at the exact same millisecond.

1.  Customer A's request reads the quantity (it's 1).
2.  Customer B's request *also* reads the quantity (it's 1).
3.  Customer A's request confirms the purchase and writes the new quantity (0).
4.  Customer B's request *also* confirms the purchase and writes the new quantity (0).

**Result:** You sold two shirts but only had one. Your state is now incorrect (`-1` if you didn't have a database constraint), and you have an angry customer.



#### **How Deep You Should Understand (Level 1)**

For this level, you **do not need to implement complex locking mechanisms**. Your goal is to understand the problem and use the standard tools provided by your database library to prevent it.

The key concept to master is the **Atomic Transaction**.

An **atomic transaction** is a sequence of operations that are guaranteed to happen all at once, or not at all. It's an "all-or-nothing" operation.

**Your focus should be on this process for the `/remove` endpoint:**

1.  **Start a transaction.**
2.  **Read** the current quantity of the product from the database.
3.  **Check** if `current_quantity >= amount_to_remove`.
4.  If the check passes, **update** the quantity in the database.
5.  **Commit the transaction.** This makes the change permanent.
6.  If the check fails (or any other error occurs), **roll back the transaction.** This undoes everything you did since step 1.

Most modern libraries like **SQLModel/SQLAlchemy** handle this for you. When you use a session to make changes and call `session.commit()`, it wraps those changes in a transaction. Your job is to make sure your "read-check-update" logic is all done within a single session context before you commit.