import mysql.connector
from mysql.connector import Error
import random 
from faker import Faker

fake = Faker()

ConnectorConf = {
    'host': 'localhost',
    'database': 'wix_test',
    'user': 'root',
    'password': 'pranav',
}

USERS_NUM = 5
PACKAGES_NUM = 28
PACKAGE_MAX = 3
ENV_NUM = 8
TIER_internal = 5  # Simulates circular dependency check by only allowing lower tier dependency

def seed():
    try:
        connector = mysql.connector.connect(**ConnectorConf)
        cursor = connector.cursor(dictionary=True)
        print("🌱 Starting Seed...")

        # 0. Clear existing data
        print("🧹 Clearing existing data...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        tables = ["APP_USER", "PACKAGE", "VERSION", "ENVIRONMENT", "ENVIRONMENT_PACKAGE", "DEPENDENCY", "CONFLICT_PAIR"]
        for table in tables:
            cursor.execute(f"TRUNCATE TABLE {table};")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        connector.commit()

        # 1. Insert Users
        users = [(i+1, fake.unique.user_name(), fake.unique.email()) for i in range(USERS_NUM)]
        cursor.executemany("INSERT INTO APP_USER (user_id, username, email) VALUES (%s, %s, %s)", users)
        connector.commit()

        # 2. Generate and Insert Packages
        packages_data = []
        for i in range(PACKAGES_NUM):
            tier = random.randint(1, TIER_internal)
            packages_data.append((i+1, fake.unique.slug().replace('-', '_'), fake.sentence(), tier))
            
        cursor.executemany("INSERT INTO PACKAGE (package_id, package_name, description) VALUES (%s, %s, %s)",
                           [(p[0], p[1], p[2]) for p in packages_data])
        connector.commit()
        
        cursor.execute("SELECT package_id FROM PACKAGE")
        pkg_ids = [row['package_id'] for row in cursor.fetchall()]
        pkg_id_to_tier = {p[0]: p[3] for p in packages_data}
        
        # 3. Generate and Insert Versions
        versions = []
        v_id_counter = 1
        for pkg_id in pkg_ids:
            num_versions = random.randint(1, PACKAGE_MAX)
            for v in range(num_versions):
                v_no = f"{v+1}.{random.randint(0, 9)}.{random.randint(0, 9)}" # Fixed comma & typo
                r_date = fake.date_between(start_date='-2y', end_date='today')
                versions.append((v_id_counter, pkg_id, v_no, r_date))
                v_id_counter += 1
                
        cursor.executemany("INSERT INTO VERSION (version_id, package_id, version_no, release_date) VALUES (%s, %s, %s, %s)", versions)
        connector.commit()
        
        # 4. Generate Dependencies (The DAG Logic)
        cursor.execute("SELECT version_id, package_id FROM VERSION") # Fixed trailing comma
        db_versions = cursor.fetchall()
        versions_by_tier = {i: [] for i in range(1, TIER_internal + 1)}
        for row in db_versions:
            versions_by_tier[pkg_id_to_tier[row['package_id']]].append(row)

        dependencies = []
        for row in db_versions:
            v_id = row['version_id']
            current_tier = pkg_id_to_tier[row['package_id']]
            
            if current_tier > 1:
                valid_packages = []
                for lower_tier in range(1, current_tier):
                    pkgs_in_tier = list(set([v['package_id'] for v in versions_by_tier[lower_tier]]))
                    valid_packages.extend(pkgs_in_tier)
                
                if valid_packages:
                    num_deps = random.randint(0, min(3, len(valid_packages)))
                    chosen_pkgs = random.sample(valid_packages, num_deps)
                    for req_pkg_id in chosen_pkgs:
                        dependencies.append((v_id, req_pkg_id, f"Requires {req_pkg_id} for core functions"))

        cursor.executemany("INSERT INTO DEPENDENCY (dependent_version_id, required_package_id, constraint_desc) VALUES (%s, %s, %s)", dependencies)
        connector.commit()

        # 5. Insert Conflict Pairs
        conflicts = []
        all_v_ids = [v['version_id'] for v in db_versions]
        for _ in range(20): 
            v1, v2 = random.sample(all_v_ids, 2)
            if v1 > v2: v1, v2 = v2, v1 # Enforce DB constraint (version_id_1 < version_id_2)
            conflicts.append((v1, v2, "Incompatible APIs"))
            
        cursor.executemany("INSERT IGNORE INTO CONFLICT_PAIR (version_id_1, version_id_2, reason) VALUES (%s, %s, %s)", conflicts)
        connector.commit()

        # 6. Insert Environments
        cursor.execute("SELECT user_id FROM APP_USER")
        user_ids = [row['user_id'] for row in cursor.fetchall()]
        envs = [(i+1, random.choice(user_ids), fake.unique.domain_word() + "_env", fake.date_this_year()) for i in range(ENV_NUM)]
        cursor.executemany("INSERT INTO ENVIRONMENT (env_id, user_id, env_name, created_at) VALUES (%s, %s, %s, %s)", envs)
        connector.commit()

        # 7. Install Random Packages (Trigger Testing)
        cursor.execute("SELECT env_id FROM ENVIRONMENT")
        env_ids = [row['env_id'] for row in cursor.fetchall()]
        
        successful_installs = 0
        trigger_blocks = 0

        for env_id in env_ids:
            target_versions = random.sample(db_versions, random.randint(10, 15))
            
            for target in target_versions:
                v_id_to_install = target['version_id']
                try:
                    cursor.execute("INSERT INTO ENVIRONMENT_PACKAGE (env_id, version_id) VALUES (%s, %s)", (env_id, v_id_to_install))
                    connector.commit()
                    successful_installs += 1
                except Error as e:
                    # Trigger caught a conflict or capacity issue
                    connector.rollback()
                    trigger_blocks += 1

        print("Seeding complete!")
        print(f"Generated {PACKAGES_NUM} packages, {len(db_versions)} versions, and {len(dependencies)} dependency links.")
        print(f"Successfully installed {successful_installs} packages into environments.")
        print(f"Database Triggers safely blocked {trigger_blocks} conflicting installations.")

    except Error as e:
        print(f"Fatal SQL Error: {e}")
    finally:
        if 'connector' in locals() and connector.is_connected():
            cursor.close()
            connector.close()

if __name__ == "__main__":
    seed()
