prompt

<details>

```

- provide context 1 + context 2


> " So from, this comtext.
As you are SE assistant for this project.
I'll tell you later what is your first query. "

> " Write full Document Requirements in detail as much as we canfor developer to implement this project.
developer can just use this Document to be direction to finish implementing.
(with canva mode) "

```

</details>

# Implementing Requirements

(Created by Gemini 2.5pro)
</br>
Here is a comprehensive Software Requirements Document (SRD) for the BKK Gadget Hub project. This document is designed to be a single source of truth for the developer, detailing everything needed for implementation.

---

### **Software Requirements Document: BKK Gadget Hub Competitor Price Scraper**

-   **Project Name:** BKK Gadget Hub - Competitor Price Scraper
-   **Version:** 1.0
-   **Date:** Friday, July 25, 2025
-   **Client:** Chaiwat S., BKK Gadget Hub
-   **Status:** **CONFIRMED**

---

### **1. Introduction**

#### **1.1 Project Overview**

This project aims to develop a custom web scraping solution to automate the collection of competitor product data for the e-commerce store "BKK Gadget Hub." The solution will target the website `powerbuy.co.th` and extract key business intelligence to inform the client's pricing strategy.

#### **1.2 The Business Problem**

> The client, Chaiwat S., currently spends 2-3 hours daily manually checking the prices and stock levels of his top 20 products on a competitor's website. This manual process is inefficient and error-prone, leading to lost revenue from uncompetitive pricing. A previous attempt to automate this with a basic scraper failed because the target site uses JavaScript to load price and stock information, a complexity the previous solution could not handle.

#### **1.3 Project Goal & Success Criteria**

-   **Primary Goal:** To completely eliminate the need for manual data collection by providing an accurate, machine-readable data file.
-   **Success Criteria:**
    -   A single, clean CSV file is delivered containing the correct data for all 20 specified products.
    -   The delivered data is 100% accurate as of the time of the scrape.
    -   The solution successfully overcomes the dynamic JavaScript-loading mechanism of the target site.

#### **1.4 Project Scope**

-   **✅ In Scope:**

    -   Developing a Python script to scrape 20 specific product pages.
    -   Extracting four defined data points: `Product Name`, `Price`, `Stock Status`, and `SKU`.
    -   Implementing logic to handle dynamically loaded content (via JavaScript).
    -   Cleaning and validating all extracted data to ensure type consistency.
    -   Delivering a final, one-time dataset in a single `.csv` file.
    -   Providing a professional Project Handoff Report in PDF format.

-   **❌ Out of Scope:**

    -   Development of a graphical user interface (GUI).
    -   Setting up a database for data storage.
    -   Deployment of the script to a cloud server or hosting environment.
    -   Configuration of automated scheduling (e.g., cron jobs).
    -   Delivery of the scraper's source code (unless purchased as a separate option).

---

### **2. Functional Requirements**

| ID        | Requirement                  | Description                                                                                                                                                                                               |
| :-------- | :--------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FR-01** | **URL Navigation**           | The system must be able to programmatically navigate to a list of provided product URLs on `https://www.powerbuy.co.th/th`.                                                                               |
| **FR-02** | **Dynamic Content Handling** | The system **must** wait for web page elements that are loaded asynchronously via JavaScript to be fully rendered before attempting to extract data. This specifically applies to Price and Stock Status. |
| **FR-03** | **Data Point Extraction**    | For each page, the system must extract the exact text or value for: 1. Product Name, 2. Price (THB), 3. Stock Status (e.g., "In Stock"), 4. SKU / Product Code.                                           |
| **FR-04** | **Input Data Source**        | The system shall receive its list of 20 target URLs from a simple text file (`urls.txt`). Each URL will be on a new line.                                                                                 |
| **FR-05** | **Output File Generation**   | The system must consolidate all scraped data and export it into a single Comma-Separated Values (`.csv`) file.                                                                                            |
| **FR-06** | **CSV File Schema**          | The output CSV must have a specific header row: `product_name,price_thb,stock_status,sku`. Each subsequent row will contain the corresponding data for one product.                                       |

---

### **3. Non-Functional Requirements**

| ID         | Requirement                      | Description                                                                                                                                                                                                                           |
| :--------- | :------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **NFR-01** | **Reliability & Error Handling** | The script must handle failures gracefully. If a single URL fails to load or an element is not found, the system should log an error for that URL and continue processing the remaining URLs without crashing.                        |
| **NFR-02** | **Data Integrity**               | All extracted data must be cleaned and validated. Specifically, prices must be converted to a numerical format (float), free of currency symbols (`฿`) and commas. All data points must be validated against the required data types. |
| **NFR-03** | **Maintainability**              | The codebase must be modular. Logic for scraping, data validation, and file I/O should be separated into distinct functions or modules to facilitate future updates. Code must be commented where logic is complex.                   |
| **NFR-04** | **Ethical Scraping Practices**   | The scraper must identify itself with a legitimate `User-Agent` string to avoid appearing as a low-quality bot. It should mimic a real browser's capabilities.                                                                        |

---

### **4. Technical Specifications**

-   **Programming Language:** Python 3.10+
-   **Core Libraries:**
    -   **Browser Automation:** `playwright` (to render JavaScript-heavy pages)
    -   **Data Validation:** `pydantic` (to define and enforce a strict data model)
    -   **Data Export:** `pandas` (to easily create the final CSV file)
-   **Execution Environment:** Local machine with Python and required libraries installed in a virtual environment (`venv`).

#### **Suggested Project Structure:**

```
bkk-gadget-scraper/
│
├── .venv/
├── main.py           # Main script: Orchestrates the entire process
├── scraper.py        # Module containing the core scraping function(s)
├── validators.py     # Module defining the Pydantic data model for a Product
├── urls.txt          # Input file containing the 20 PowerBuy product URLs
├── requirements.txt  # Lists all Python package dependencies (playwright, pydantic, pandas)
└── output/
    └── competitor_prices_YYYY-MM-DD.csv # Final deliverable is placed here
```

#### **Execution Flow Diagram:**

1.  **Start `main.py`**
2.  **Read** URLs from `urls.txt` into a list.
3.  **Initialize** an empty list to store results.
4.  **Loop** through each URL:
    -   Call `scrape_product_data(url)` from `scraper.py`.
    -   `scraper.py` uses Playwright to launch a browser, navigate, `page.wait_for_selector()` for price/stock, and extract raw text.
    -   Return raw data dictionary.
    -   In `main.py`, pass the raw data to the `Product` model from `validators.py`. This step cleans and validates the data.
    -   Append the validated Pydantic object to the results list.
    -   _If error:_ Log the failed URL and continue the loop.
5.  **After Loop:**
    -   Use `pandas` to convert the list of Pydantic objects into a DataFrame.
    -   Save the DataFrame to a `.csv` file in the `output/` directory with the correct filename.
6.  **End**

---

### **5. Deliverables & Timeline**

| Date                         | Day | Milestone                   | Deliverable(s)                                                                      |
| :--------------------------- | :-- | :-------------------------- | :---------------------------------------------------------------------------------- |
| **Fri, Jul 25**              | 1   | Project Kickoff             | Formal proposal acceptance.                                                         |
| **Mon, Jul 28 - Fri, Aug 1** | 2-6 | Core Development Sprint     | Implementation of the scraper script as per this document.                          |
| **Mon, Aug 4**               | 7   | **Client Milestone Review** | `BKK_Gadget_Hub_Sample.csv` (with data for 5 products).                             |
| **Tue, Aug 5 - Wed, Aug 6**  | 8-9 | Finalization                | Execution of the scraper for all 20 URLs.                                           |
| **Thu, Aug 7**               | 10  | Package Preparation         | `Project Handoff Report.pdf` written; final assets compiled.                        |
| **Fri, Aug 8**               | 11  | **FINAL DELIVERY**          | `competitor_prices_2025-08-08.csv` & `Project Handoff Report.pdf` in a ZIP archive. |
