-- ==========================================
-- DBMS Project: Wix (Package Management System)
-- Seed Data for Testing (MySQL)
-- Matches the True Schema with APP_USER and CONFLICT_PAIR
-- ==========================================

USE wix_test;

-- INSERT APP_USERS
INSERT INTO APP_USER (username, email) VALUES
('alice', 'alice@wix.com'),
('bob', 'bob@wix.com'),
('charlie', 'charlie@wix.com');

-- INSERT PACKAGES
-- We need some 'graphics' packages to satisfy Query 1
INSERT INTO PACKAGE (package_name, description) VALUES
('numpy', 'Fundamental package for scientific computing with Python'),
('pandas', 'Data analysis and manipulation tool'),
('matplotlib', 'Python 2D graphics and plotting library'),
('pillow', 'Python Imaging Library for graphics processing'),
('scikit-learn', 'Machine learning in Python'),
('tensorflow', 'End-to-end open source machine learning platform'),
('python3.9', 'Python Runtime Environment'),
('python3.10', 'Python Runtime Environment');

-- INSERT VERSIONS
-- We need versions in 2025 to satisfy Query 2, and enough data for rankings (Query 14)
INSERT INTO VERSION (package_id, version_no, release_date) VALUES
(1, '1.24.0', '2025-01-15'), -- 1: numpy 1.24
(1, '1.25.0', '2025-06-20'), -- 2: numpy 1.25
(2, '2.0.0', '2025-02-10'),  -- 3: pandas 2.0
(2, '2.1.0', '2025-08-05'),  -- 4: pandas 2.1
(3, '3.7.0', '2025-03-12'),  -- 5: matplotlib
(4, '10.0.0', '2025-04-01'), -- 6: pillow
(5, '1.3.0', '2024-11-20'),  -- 7: scikit-learn
(6, '2.14.0', '2025-09-10'), -- 8: tensorflow
(7, '3.9.16', '2023-12-01'), -- 9: python 3.9
(8, '3.10.12', '2024-05-01');-- 10: python 3.10


-- INSERT ENVIRONMENTS (Multiple environments per user allowed)
INSERT INTO ENVIRONMENT (user_id, env_name, created_at) VALUES
(1, 'alice_env_1', '2025-01-01'), -- env_id: 1 (Alice)
(1, 'alice_env_2', '2025-02-01'), -- env_id: 2 (Alice)
(2, 'bob_env', '2025-03-01');     -- env_id: 3 (Bob)

-- INSERT DEPENDENCIES
-- (dependent_version_id, required_package_id, constraint_desc)
-- Meaning: "This specific version of a package requires SOME version of this other package"
INSERT INTO DEPENDENCY (dependent_version_id, required_package_id, constraint_desc) VALUES
(3, 1, 'Pandas 2.0 requires numpy'),
(4, 1, 'Pandas 2.1 requires numpy'),
(5, 1, 'Matplotlib 3.7 requires numpy'),
(7, 1, 'Scikit-learn requires numpy'),
(8, 1, 'Tensorflow requires numpy'),
(7, 2, 'Scikit-learn requires pandas'),
(8, 5, 'Tensorflow requires scikit-learn'); -- Creates dependency chain

-- INSERT CONFLICT PAIRS
-- (version_id_1, version_id_2, reason) Ensure id_1 < id_2
-- Example: Python 3.9 (id 9) conflicts with Python 3.10 (id 10)
INSERT INTO CONFLICT_PAIR (version_id_1, version_id_2, reason) VALUES
(9, 10, 'Cannot have two minor versions of Python in the same environment'),
(1, 2, 'Cannot have numpy 1.24 and 1.25 at the same time');

-- INSERT ENVIRONMENT_PACKAGE (Direct installations, NO snapshots)
-- alice_env_1 (env 1): python 3.10, numpy 1.25, pandas 2.1
INSERT INTO ENVIRONMENT_PACKAGE (env_id, version_id, is_active) VALUES
(1, 10, 1),
(1, 2, 1),
(1, 4, 1);

-- alice_env_2 (env 2): python 3.9, numpy 1.24, scikit-learn 1.3
INSERT INTO ENVIRONMENT_PACKAGE (env_id, version_id, is_active) VALUES
(2, 9, 1),
(2, 1, 1),
(2, 7, 1);

-- bob_env (env 3): python 3.10, numpy 1.25, matplotlib 3.7
INSERT INTO ENVIRONMENT_PACKAGE (env_id, version_id, is_active) VALUES
(3, 10, 1),
(3, 2, 1),
(3, 5, 1);

-- Setup base conditions for Query 13 (Recursive Dependency)
INSERT INTO VERSION (version_id, package_id, version_no, release_date) VALUES
(42, 6, '2.15.0', '2025-10-01');

INSERT INTO DEPENDENCY (dependent_version_id, required_package_id, constraint_desc) VALUES
(42, 1, 'TF 2.15 needs Numpy'), 
(42, 5, 'TF 2.15 needs Scikit-Learn');
