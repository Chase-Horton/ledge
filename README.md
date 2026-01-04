<!--[![Pytest](https://img.shields.io/badge/Pytest-fff?logo=pytest&logoColor=000)](https://docs.pytest.org/en/stable/)
[![uv](https://img.shields.io/badge/Managed_by_uv-8333E9?logo=python&logoColor=fff&labelColor=8333E9)](#)-->
# ledge
[![Unit Tests](https://github.com/Chase-Horton/ledge/actions/workflows/ci.yml/badge.svg)](https://github.com/Chase-Horton/ledge/actions/workflows/ci.yml)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Chase-Horton/9200639f20a97b64ce3093a62636e16e/raw/coverage.json)
[![Python](https://img.shields.io/badge/Python-3.8+-gray?logo=python&logoColor=fff&labelColor=3776AB)](https://www.python.org/)

`ledge` is a Python-based accounting framework designed for developers, and businesses who want full ownership of their financial data without the performance bottlenecks of text files or the privacy nightmares of the cloud.
## Philosophy
### The Problem
Currently the accounting software landscape is split into two extremes.
1. **Plain Text Accounting**: tools like `beancount`, `ledger`, `hledger`
  - Pros: Great for version control, easy to understand format
  - Cons: Parsing large histories is slow, data integrity is questionable as it does not rely on any source of truth, stock pricing and stock splits are obtuse and complex, storing historical pricing data in text files is archaic
2. **SaaS/Cloud Accounting**: tools like Quicken, Xero, or Mint
  - Pros: Simple to use, automated transaction recording, accesible anywhere
  - Cons: You do not own your data, exporting can be difficult, and you are subject to changes in pricing or policy
### The Solution
Double Entry accounting is relational by nature, by utilizing a local SQL database we gain:
  - Speed: Standard SQL indexing prevents having to slowly parse large text files
  - Integrity: ACID compliance and foreign key constraints act ensure ledger is balanced at a database level
  - Standardization: No domain specific language needs to be known, its just SQL, and can be analyzed in any of the available SQL client
## Project Goals
1. **Strict Double-Entry Accounting**:Assets + Liabilites + Income + Expense + Equity = 0
2. **Local First**:No backend required, default is SQLite, with support for PostgreSQL or MySQL
3. **Import API**: Robust API for scripting imports from various financial institutions
4. **Command Line Tool**: Tool for quickly producing balance sheets, income statements, and custom reports
5. **Commodity Pricing**: Associate a commodity price with a ticker to have market value reflected on historical charts automatically.
