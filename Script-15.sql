/* =========================================================================
   WIX PACKAGE MANAGER - TRANSACTION DEMONSTRATIONS
   ========================================================================= */

/* -------------------------------------------------------------------------
   DEMO 1: The Conflict Rollback (The one you already tested)
   Goal: Prove that if a multi-package install hits a conflict, the safe 
         packages are rolled back and not left orphaned.
   Prerequisite: Env 1 must be empty of Versions 2 and 11.
------------------------------------------------------------------------- */

-- [RUN THIS TO PROVE BASELINE]
SELECT * FROM ENVIRONMENT_PACKAGE WHERE env_id = 1;

-- [RUN THIS TO START]
START TRANSACTION;
INSERT INTO ENVIRONMENT_PACKAGE (env_id, version_id) VALUES (1, 2); -- Success

-- [RUN THIS TO TRIGGER FAILURE]
INSERT INTO ENVIRONMENT_PACKAGE (env_id, version_id) VALUES (1, 11); -- FAILS (Trigger 1: Conflict)

-- [RUN THIS TO PROVE ATOMICITY]
ROLLBACK;
SELECT * FROM ENVIRONMENT_PACKAGE WHERE env_id = 1; 
-- Notice Version 2 is gone. The transaction saved the environment from corruption.


/* -------------------------------------------------------------------------
   DEMO 2: Environment Initialization (The Ghost Environment Prevention)
   Goal: Prove that if an environment is created, but its base packages 
         fail to install, the empty "ghost" environment is destroyed.
   Prerequisite: You need to know a valid user_id (e.g., 1) and a valid 
                 version_id (e.g., 1). We will use a fake version (9999) to force a crash.
------------------------------------------------------------------------- */

-- [RUN THIS TO START]
START TRANSACTION;

-- Create the new environment
INSERT INTO ENVIRONMENT (user_id, env_name, created_at) 
VALUES (1, 'Data_Science_Base', CURDATE());

-- Grab the ID of the environment we JUST created
SET @new_env_id = LAST_INSERT_ID();

-- Install the first base package
INSERT INTO ENVIRONMENT_PACKAGE (env_id, version_id) VALUES (@new_env_id, 1); -- Success

-- [RUN THIS TO TRIGGER FAILURE]
-- Try to install a package that doesn't exist (violates Foreign Key constraint)
INSERT INTO ENVIRONMENT_PACKAGE (env_id, version_id) VALUES (@new_env_id, 99999); -- FAILS

-- [RUN THIS TO PROVE ATOMICITY]
ROLLBACK;

-- Check if the 'Data_Science_Base' environment exists
SELECT * FROM ENVIRONMENT WHERE env_name = 'Data_Science_Base';
-- The result is empty. The rollback destroyed the environment because the setup failed.


/* -------------------------------------------------------------------------
   DEMO 3: The Data Integrity Block (Testing Trigger 2: Self-Dependency)
   Goal: Prove that if a user registers a new package version, but accidentally 
         makes it depend on itself, the system rolls back the version creation.
   Prerequisite: We need a valid package_id (e.g., 5).
------------------------------------------------------------------------- */

-- [RUN THIS TO PROVE BASELINE]
SELECT * FROM VERSION WHERE version_no = '99.9.9';

-- [RUN THIS TO START]
START TRANSACTION;

-- Create a brand new version for Package ID 5
INSERT INTO VERSION (package_id, version_no, release_date) 
VALUES (5, '99.9.9', CURDATE());

-- Grab the ID of the version we JUST created
SET @new_version_id = LAST_INSERT_ID();

-- [RUN THIS TO TRIGGER FAILURE]
-- Try to make this new version depend on its own base package (Package 5)
INSERT INTO DEPENDENCY (dependent_version_id, required_package_id, constraint_desc) 
VALUES (@new_version_id, 5, 'Requires itself'); -- FAILS (Trigger 2: Self-Dependency)

-- [RUN THIS TO PROVE ATOMICITY]
ROLLBACK;

SELECT * FROM VERSION WHERE version_no = '99.9.9';
-- The result is empty. The system wiped out the bad version data.