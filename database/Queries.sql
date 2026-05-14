-- ==========================================
-- DBMS Project: Wix (Package Management System)
-- Group: 114 | T.A: Utkarsh Agarwal
-- Members: Pranav Sethi, Nandini Rana, laikansh Bansal
-- Task 4: Queries
-- ==========================================

-- ==========================================
-- BASIC QUERIES (3)
-- Concepts: Selection, Projection, Aggregation
-- ==========================================

-- 1. Search for a specific package category (String Matching)
USE wix_test;

SELECT package_id, package_name, description 
FROM PACKAGE 
WHERE description LIKE '%graphics%';

-- 2. List versions within a specific release window (Range Predicates)
SELECT version_id, version_no 
FROM VERSION 
WHERE release_date BETWEEN '2025-01-01' AND '2025-12-31';

-- 3. Count installed versions per environment (Aggregation)

SELECT env_id, COUNT(version_id) AS installed_count
FROM ENVIRONMENT_PACKAGE
GROUP BY env_id;


-- ==========================================
-- PART 2: INTERMEDIATE QUERIES (6)
-- Concepts: Joins, Set Operations, Group Filtering
-- ==========================================

-- 4. Find environments with too many packages (Filtering Groups)
SELECT env_id, COUNT(version_id) AS installed_count
FROM ENVIRONMENT_PACKAGE
GROUP BY env_id
HAVING COUNT(version_id) > 50;

-- 5. Find packages common to two different environments (Set Intersection)
(SELECT version_id FROM ENVIRONMENT_PACKAGE WHERE env_id = 1)
INTERSECT
(SELECT version_id FROM ENVIRONMENT_PACKAGE WHERE env_id = 2);

-- 6. Find missing dependencies between environments (Set Difference)
(SELECT version_id FROM ENVIRONMENT_PACKAGE WHERE env_id = 1)
EXCEPT
(SELECT version_id FROM ENVIRONMENT_PACKAGE WHERE env_id = 2);

-- 7. Find standalone versions with zero dependencies (Anti-Join)

SELECT version_id, version_no 
FROM VERSION V
WHERE NOT EXISTS (
    SELECT * FROM DEPENDENCY D 
    WHERE D.dependent_version_id = V.version_id
);

-- 8. Find the package with the highest number of versions (Set Comparison)

SELECT package_id 
FROM VERSION 
GROUP BY package_id
HAVING COUNT(version_id) >= ALL (
    SELECT COUNT(version_id) 
    FROM VERSION 
    GROUP BY package_id
);

-- 9. Show the full name of every installed package in an environment (Multi-Table Join)

SELECT E.env_name, P.package_name, V.version_no
FROM ENVIRONMENT E
INNER JOIN ENVIRONMENT_PACKAGE EP ON E.env_id = EP.env_id
INNER JOIN VERSION V ON EP.version_id = V.version_id
INNER JOIN PACKAGE P ON V.package_id = P.package_id;


-- ==========================================
-- ADVANCED QUERIES (6)
-- Concepts: Relational Division, OLAP, Recursion
-- ==========================================

-- 10. Find a package installed in EVERY environment (Relational Division)
SELECT version_id FROM VERSION V
WHERE NOT EXISTS (
    SELECT env_id FROM ENVIRONMENT E
    EXCEPT
    SELECT env_id FROM ENVIRONMENT_PACKAGE EP WHERE EP.version_id = V.version_id
);

-- 11. Hide underlying complexity with a View
CREATE VIEW environment_summary AS
SELECT E.env_name, COUNT(EP.version_id) as total_packages
FROM ENVIRONMENT E
JOIN ENVIRONMENT_PACKAGE EP ON E.env_id = EP.env_id
GROUP BY E.env_name;

-- 12. Tells all conflicting packages active inside any environment.
SELECT DISTINCT
    E.env_name, 
    P1.package_name AS installed_pkg_1,
    V1.version_no AS version_1,
    P2.package_name AS conflicting_pkg_2,
    V2.version_no AS version_2
FROM ENVIRONMENT E
JOIN ENVIRONMENT_PACKAGE EP1 ON E.env_id = EP1.env_id
JOIN CONFLICT_PAIR CP ON EP1.version_id = CP.version_id_1
JOIN ENVIRONMENT_PACKAGE EP2 ON E.env_id = EP2.env_id 
                            AND CP.version_id_2 = EP2.version_id
JOIN VERSION V1 ON EP1.version_id = V1.version_id
JOIN PACKAGE P1 ON V1.package_id = P1.package_id
JOIN VERSION V2 ON EP2.version_id = V2.version_id
JOIN PACKAGE P2 ON V2.package_id = P2.package_id
WHERE EP1.is_active = 1 
  AND EP2.is_active = 1
  AND EP1.version_id < EP2.version_id;

-- 13. Recursive Dependency Resolution
-- Concept: Using a 'recursive' view definition to compute transitive closure.

WITH RECURSIVE dependency_tree(dependent_version_id, required_package_id) AS (
    -- Base case
    SELECT dependent_version_id, required_package_id
    FROM DEPENDENCY
    WHERE dependent_version_id = 42 
    
    UNION
    
    -- Recursive step
    SELECT DT.dependent_version_id, D.required_package_id
    FROM dependency_tree DT
    JOIN VERSION V ON DT.required_package_id = V.package_id
    JOIN DEPENDENCY D ON V.version_id = D.dependent_version_id
)
SELECT DISTINCT * FROM dependency_tree;

-- 14. Find users running outdated package versions (Nested Subqueries & Multi-Joins)
SELECT 
    U.username, 
    E.env_name, 
    P.package_name, 
    V.version_no AS installed_version,
    V.release_date AS installed_date
FROM APP_USER U
JOIN ENVIRONMENT E ON U.user_id = E.user_id
JOIN ENVIRONMENT_PACKAGE EP ON E.env_id = EP.env_id
JOIN VERSION V ON EP.version_id = V.version_id
JOIN PACKAGE P ON V.package_id = P.package_id
WHERE V.release_date < (
    SELECT MAX(release_date) 
    FROM VERSION V2 
    WHERE V2.package_id = P.package_id
)
ORDER BY U.username, P.package_name;

-- 15. Hierarchical Summary of Installations (OLAP Rollup)
SELECT E.env_name, V.version_no, COUNT(*) as count
FROM ENVIRONMENT_PACKAGE EP
JOIN ENVIRONMENT E ON EP.env_id = E.env_id
JOIN VERSION V ON EP.version_id = V.version_id
GROUP BY E.env_name, V.version_no WITH ROLLUP;


ALTER TABLE APP_USER MODIFY user_id INTEGER AUTO_INCREMENT;