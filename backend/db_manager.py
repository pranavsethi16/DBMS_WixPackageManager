import os
from streamlit_agraph import agraph, Node, Edge, Config
from collections import defaultdict
# To install: pip install mysql-connector-python
import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    def __init__(self, host='localhost', database='wix_test', user='root', password='pranav'):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        """Establish connection to the MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                print(f"Connected to MySQL Database: {self.database}")
                return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False

    def close(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed.")

    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results."""
        if not self.connection or not self.connection.is_connected():
            print("Not connected to database.")
            return None

        cursor = self.connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # If it's a SELECT query, return the rows
            if query.strip().upper().startswith("SELECT") or query.strip().upper().startswith("WITH") or query.strip().upper().startswith("("):
                return cursor.fetchall()
            
            # If it's an INSERT/UPDATE/DELETE, commit it
            self.connection.commit()
            return cursor.lastrowid
            
        except Error as e:
            print(f"SQL Error: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    # --- Methods specifically mapped to Task 4 Queries ---

    def query_1_search_packages(self, keyword):
        """Basic Query (1): Search for packages containing a string."""
        sql = "SELECT package_id, package_name, description FROM PACKAGE WHERE package_name LIKE %s"
        return self.execute_query(sql, (f"%{keyword}%",))

    def query_9_env_packages(self):
        """Intermediate Query (9): Show full name of installed packages via Multi-Table Join."""
        sql = '''
            SELECT E.env_name, P.package_name, V.version_no
            FROM ENVIRONMENT E
            INNER JOIN ENVIRONMENT_PACKAGE EP ON E.env_id = EP.env_id
            INNER JOIN VERSION V ON EP.version_id = V.version_id
            INNER JOIN PACKAGE P ON V.package_id = P.package_id;
        '''
        return self.execute_query(sql)

    def query_11_get_environment_summary(self):
        """Advanced Query (11): Hide complexity using a View."""
        # Note: Ensure the view is created in the DB first before calling this!
        sql = "SELECT * FROM environment_summary;"
        return self.execute_query(sql)

    def query_13_recursive_dependencies(self, version_id):
        """Advanced Query (13): Recursive CTE for deep dependency resolution."""
        sql = '''
            WITH RECURSIVE dependency_tree(dependent_version_id, required_package_id) AS (
                SELECT dependent_version_id, required_package_id
                FROM DEPENDENCY
                WHERE dependent_version_id = %s
                
                UNION
                
                SELECT DT.dependent_version_id, D.required_package_id
                FROM dependency_tree DT
                JOIN VERSION V ON DT.required_package_id = V.package_id
                JOIN DEPENDENCY D ON V.version_id = D.dependent_version_id
            )
            SELECT DISTINCT * FROM dependency_tree;
        '''
        return self.execute_query(sql, (version_id,))


    def get_all_environments(self):
        """Fetch all available environments for UI dropdowns."""
        sql = "SELECT env_id, env_name FROM ENVIRONMENT ORDER BY env_id"
        return self.execute_query(sql)

    def get_all_versions(self):
        """Fetch all available package versions for UI dropdowns."""
        sql = '''
            SELECT V.version_id, P.package_name, V.version_no
            FROM VERSION V
            JOIN PACKAGE P ON V.package_id = P.package_id
            ORDER BY P.package_name, V.version_no
        '''
        return self.execute_query(sql)

    # --- Task 5: Application Logic & Trigger Testing ---

    def test_trigger_install_package(self, env_id, version_id):
        """
        Attempts to install a package into an environment.
        This deliberately tests Triggers 1 and 2.
        """
        print(f"\nAttempting to install Version {version_id} into Environment {env_id}...")
        
        sql = "INSERT INTO ENVIRONMENT_PACKAGE (env_id, version_id, is_active) VALUES (%s, %s, %s)"
        
        if not self.connection or not self.connection.is_connected():
            return "Connection error"

        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, (env_id, version_id, 1))
            self.connection.commit()
            print("SUCCESS: Package installed successfully.")
            return True
            
        except Error as e:
            print("=========================================")
            print(f"🚫 TRIGGER BLOCKED INSTALLATION")
            print(f"Error Code: {e.errno}")
            print(f"Error Message: {e.msg}")
            print("=========================================")
            self.connection.rollback()
            return False
            
        finally:
            cursor.close()
    
    def query_dependency_graph_data(self):
        """
        Fetches all dependency relationships to build the network graph.
        Returns a list of dicts with version and required package details.
        """
        query = """
            SELECT 
                v.version_id,
                p_v.package_name AS dependent_pkg_name,
                v.version_no AS dependent_version_no,
                d.required_package_id,
                p_req.package_name AS required_pkg_name,
                d.constraint_desc
            FROM DEPENDENCY d
            JOIN VERSION v ON d.dependent_version_id = v.version_id
            JOIN PACKAGE p_v ON v.package_id = p_v.package_id
            JOIN PACKAGE p_req ON d.required_package_id = p_req.package_id;
        """
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

# Example usage (This acts as the CLI/Testing layer for now)
if __name__ == "__main__":
    
    print("--- Wix Database Manager Application ---")
    
    # You will need to change 'password' to your actual MySQL root password
    # e.g. db = DatabaseManager(password="your_root_password")
    db = DatabaseManager('localhost', 'wix_test', 'root', 'pranav')
    
    if db.connect():
        print("\n--- Testing Query 1 (Search Packages) ---")
        results = db.query_1_search_packages('graphics')
        for r in results:
            print(r)
            
        print("\n--- Testing Query 9 (Environment Packages) ---")
        results = db.query_9_env_packages()
        for r in results:
            print(r)
            
        print("\n--- Testing Query 13 (Recursive Dependencies for Version 42) ---")
        results = db.query_13_recursive_dependencies(42)
        if results:
            for r in results:
                print(r)
        else:
            print("No dependencies found or Query returned None.")

        print("\n--- Testing Trigger Exceptions (Task 5: Triggers) ---")
        
        # Test 1: Conflicts Trigger
        # bob_env (env_id = 3) currently has Python 3.10 (version_id = 10)
        # CONFLICT_PAIR (9, 10) explicitly says they conflict.
        # Installing Python 3.9 (version_id = 9) should trigger a block.
        print("\nTest 1: Installing Python 3.9 into Env 3 (Should fail due to Conflict with Python 3.10)")
        db.test_trigger_install_package(3, 9)

        # Test 2: Dependency Trigger
        # pandas 2.1 (version_id = 4) REQUIRES numpy (package_id = 1)
        # We will try installing Pandas 2.1 into a brand new empty environment (which doesn't have numpy)
        # First, let's create a temporary empty environment.
        db.execute_query("INSERT INTO ENVIRONMENT (user_id, env_name, created_at) VALUES (1, 'empty_test_env', '2026-01-01')")
        empty_env_id = db.execute_query("SELECT MAX(env_id) as env_id FROM ENVIRONMENT")[0]['env_id']
        
        print(f"\nTest 2: Installing Pandas 2.1 into Empty Env {empty_env_id} (Should fail due to missing Numpy dependency)")
        db.test_trigger_install_package(empty_env_id, 4)
        
        # Cleanup
        db.execute_query(f"DELETE FROM ENVIRONMENT WHERE env_id = {empty_env_id}")

        db.close()
