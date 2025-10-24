import os
import subprocess
import getpass
import time
import itertools
import threading
from datetime import datetime
import json
import glob

try:
    import oracledb
except ImportError:
    print("Error: The 'oracledb' library is not installed.")
    print("Please install it using: pip install oracledb")
    exit(1)

class Spinner:
    """A simple text-based loading spinner."""
    def __init__(self, message="Loading...", delay=0.1):
        self.spinner = itertools.cycle(r'-\|/')
        self.delay = delay
        self.busy = False
        self.spinner_visible = False
        self.message = message
        self.thread = None

    def _run(self):
        while self.busy:
            print(f'\r{self.message} {next(self.spinner)}', end='')
            self.spinner_visible = True
            time.sleep(self.delay)

    def start(self):
        self.busy = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def stop(self):
        self.busy = False
        if self.thread:
            self.thread.join()
        if self.spinner_visible:
            print('\r' + ' ' * (len(self.message) + 2) + '\r', end='')

def get_db_credentials():
    """Prompts the user for database connection details."""
    print("\nPlease enter your Oracle database connection details:")
    db_user = input("User: ")
    db_password = getpass.getpass("Password: ")
    db_host = input("Host (e.g., localhost): ")
    db_port = input("Port (e.g., 1521): ")
    db_service = input("Service Name (e.g., orcl): ")
    
    dsn = f"{db_host}:{db_port}/{db_service}"
        
    return db_user, db_password, dsn

def get_schemas(user, password, dsn):
    """Connects to the DB and fetches a list of schemas."""
    spinner = Spinner("Connecting to database and fetching schemas...")
    spinner.start()
    start_time = time.time()
    try:
        with oracledb.connect(user=user, password=password, dsn=dsn) as connection:
            with connection.cursor() as cursor:
                sql = "SELECT username FROM dba_users WHERE account_status = 'OPEN' AND default_tablespace <> 'SYSTEM' ORDER BY username"
                cursor.execute(sql)
                schemas = [row[0] for row in cursor.fetchall()]
                return schemas
    except oracledb.Error as e:
        print(f"\nError connecting to database or fetching schemas: {e}")
        return None
    finally:
        spinner.stop()
        end_time = time.time()
        print(f"Completed in {end_time - start_time:.2f} seconds.")

def select_schema(schemas):
    """Displays the list of schemas and prompts the user to select one."""
    print("\nPlease select a schema to export:")
    for i, schema in enumerate(schemas):
        print(f"{i + 1}. {schema}")

    while True:
        try:
            choice = int(input("Enter the number of the schema: "))
            if 1 <= choice <= len(schemas):
                return schemas[choice - 1]
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def create_impdp_details_file(user, password, dsn, schema):
    """Creates a JSON file with details for the import process."""
    print(f"\nCreating impdp details file for schema: {schema}...")
    spinner = Spinner("Fetching schema details...")
    spinner.start()
    start_time = time.time()
    try:
        with oracledb.connect(user=user, password=password, dsn=dsn) as connection:
            with connection.cursor() as cursor:
                # Get schema name and default tablespace
                sql_user = "SELECT username, default_tablespace FROM dba_users WHERE username = :schema"
                cursor.execute(sql_user, schema=schema)
                user_details = cursor.fetchone()
                if not user_details:
                    print(f"\nError: Schema '{schema}' not found.")
                    return None, None

                # Get Data Pump directory path
                sql_dir = "SELECT directory_path FROM dba_directories WHERE directory_name = 'DATA_PUMP_DIR'"
                cursor.execute(sql_dir)
                dir_path = cursor.fetchone()
                if not dir_path:
                    print("\nError: DATA_PUMP_DIR not found.")
                    return None, None

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dump_filename = f"{schema}_{timestamp}.dmp"
                config_filename = f"impdp_details_{schema}_{timestamp}.json"

                impdp_details = {
                    "schema_name": user_details[0],
                    "default_tablespace": user_details[1],
                    "data_pump_dir": dir_path[0],
                    "dump_file": dump_filename,
                }

                with open(config_filename, 'w') as f:
                    json.dump(impdp_details, f, indent=4)

                print(f"\nSuccessfully created impdp details file: {config_filename}")
                return config_filename, dump_filename

    except oracledb.Error as e:
        print(f"\nError creating impdp details file: {e}")
        return None, None
    finally:
        spinner.stop()
        end_time = time.time()
        print(f"Completed in {end_time - start_time:.2f} seconds.")

def run_export(user, password, dsn, schema, dump_filename):
    """Constructs and runs the expdp command, showing real-time output."""
    print(f"\nStarting export for schema: {schema}...")
    start_time = time.time()
    
    log_filename_expdp = f"{os.path.splitext(dump_filename)[0]}.log"
    
    log_dir = "log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename_local = os.path.join(log_dir, log_filename_expdp)
    
    
    connection_string = f"{user}/{password}@{dsn}"
    
    command = [
        'expdp',
        connection_string,
        f"schemas={schema}",
        f"dumpfile={dump_filename}",
        f"logfile={log_filename_expdp}"
    ]

    
    print("\nGenerated command:")
    print(" ".join(command) + "\n")

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        print("--- expdp Log ---")
        with open(log_filename_local, 'w') as log_file:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                print(line, end='')
                log_file.write(line)
        
        process.wait()
        print("--- End of Log ---")

        if process.returncode == 0:
            print("\nExport completed successfully.")
            return dump_filename, log_filename_local
        else:
            print(f"\nError: expdp process exited with return code {process.returncode}")
            return None, None

    except FileNotFoundError:
        print("\nError: 'expdp' command not found.")
        print("Please ensure the Oracle Database utilities are in your system's PATH.")
        return None, None
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return None, None
    finally:
        end_time = time.time()
        print(f"Total export process time: {end_time - start_time:.2f} seconds.")

def run_export_workflow():
    """Runs the entire export process."""
    print("\n--- Oracle Database Export Tool ---")
    db_user, db_password, dsn = get_db_credentials()

    schemas = get_schemas(db_user, db_password, dsn)

    if not schemas:
        print("Could not fetch schemas. Exiting.")
        return

    selected_schema = select_schema(schemas)
    print(f"\nYou have selected schema: {selected_schema}")

    config_filename, dump_filename = create_impdp_details_file(db_user, db_password, dsn, selected_schema)

    if not config_filename:
        print("Could not create impdp details file. Exiting.")
        return

    dump_file, log_file = run_export(db_user, db_password, dsn, selected_schema, dump_filename)

    if dump_file and log_file:
        print("\n--- Export Summary ---")
        print(f"Schema:    {selected_schema}")
        print(f"Dump file: {dump_file}")
        print(f"Log file:  {log_file}")
        print(f"Config file: {config_filename}")
        print("\nTool execution finished successfully.")
    else:
        print("\nTool execution failed.")

def main():
    """Main function to run the Oracle export tool."""
    print("--- Oracle Database Export Tool ---")
    run_export_workflow()


if __name__ == "__main__":
    main()