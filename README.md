# Oracle Pump CLI

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Version](https://img.shields.io/badge/version-v1.0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
[![Last Commit](https://img.shields.io/github/last-commit/srohit619/oracle-pump-cli)](https://github.com/srohit619/oracle-pump-cli/commits/main)

A command-line utility to automate Oracle Data Pump (expdp) operations for fast and repeatable database schema exports.

## Description

This script provides a simple and interactive way to export Oracle database schemas. It guides the user through the process of selecting a schema and then generates and executes the `expdp` command. The script also saves the export log for future reference.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/srohit619/oracle-pump-cli.git
    cd oracle-pump-cli
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    -   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    -   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Use

1.  **Run the script:**
    ```bash
    python orcl_impexp.py
    ```

2.  **Enter the database connection details:**
    The script will prompt you to enter the database user, password, host, port, and service name.

3.  **Select a schema to export:**
    The script will display a list of available schemas. Select the schema you want to export by entering the corresponding number.

4.  **Export process:**
    The script will then run the `expdp` command to export the selected schema. The export log will be saved in the `log` directory.

## Future Features

-   **Import functionality:** The ability to import a schema from a dump file.