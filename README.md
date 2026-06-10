##Note: This is the current iteration and has to be updated

# Wix Package Manager

A package management and dependency tracking system built using MySQL, Python, and Streamlit. The project simulates how package managers maintain software environments, resolve dependencies, detect conflicts, and ensure database consistency through triggers and transactions.

## Features

- Search packages by keyword
- View installed packages across environments
- Explore recursive dependency trees
- Install package versions into environments
- Detect dependency violations using database triggers
- Prevent conflicting package installations
- Interactive dependency graph visualization
- Transaction demonstrations for rollback and atomicity

## Tech Stack

- Python
- MySQL
- Streamlit
- Faker
- Pandas
- Recursive SQL (CTE)

## Database Concepts Demonstrated

- Relational Schema Design
- Primary and Foreign Keys
- Triggers
- Transactions
- ACID Properties
- Recursive Queries
- Multi-table Joins
- Data Integrity Constraints

## System Components

### Package Management
Stores packages, versions, dependencies, and conflict relationships.

### Environment Management
Maintains isolated software environments with installed package versions.

### Dependency Resolution
Uses recursive SQL queries to retrieve complete dependency trees.

### Conflict Detection
Database triggers prevent installation of incompatible package versions.

### Graph Visualization
Interactive dependency network showing package relationships.

## Running the Project

### Install Dependencies

```bash
pip install streamlit pandas mysql-connector-python faker streamlit-agraph
