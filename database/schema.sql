-- ==========================================
-- DBMS Project: Wix (Package Management System)
-- Schema Definition (MySQL)
-- Ground Truth
-- ==========================================
 -- Protects your current session
DROP DATABASE wix_test;
CREATE DATABASE IF NOT EXISTS wix_test;
USE wix_test;

CREATE TABLE APP_USER (
    user_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

ALTER TABLE APP_USER MODIFY user_id INTEGER AUTO_INCREMENT;

CREATE TABLE PACKAGE (
    package_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    package_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE VERSION (
    version_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    package_id INTEGER NOT NULL,
    version_no VARCHAR(50) NOT NULL,
    release_date DATE,
    FOREIGN KEY(package_id) REFERENCES PACKAGE(package_id) 
        ON DELETE CASCADE
);

-- Index for performance on release_date
CREATE INDEX idx_version_release_date ON VERSION(release_date);

CREATE TABLE ENVIRONMENT (
    env_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    env_name VARCHAR(100) NOT NULL,
    created_at DATE NOT NULL,
    FOREIGN KEY(user_id) REFERENCES APP_USER(user_id)
        ON DELETE CASCADE
);

-- Index for performance on env_name
CREATE INDEX idx_env_name ON ENVIRONMENT(env_name);

CREATE TABLE ENVIRONMENT_PACKAGE (
    env_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,
    PRIMARY KEY(env_id, version_id),
    FOREIGN KEY(env_id) REFERENCES ENVIRONMENT(env_id) 
        ON DELETE CASCADE,
    FOREIGN KEY(version_id) REFERENCES VERSION(version_id) 
        ON DELETE CASCADE
);

CREATE TABLE DEPENDENCY (
    dependent_version_id INTEGER NOT NULL,
    required_package_id INTEGER NOT NULL,
    constraint_desc VARCHAR(255),
    PRIMARY KEY (dependent_version_id, required_package_id),
    FOREIGN KEY(dependent_version_id) REFERENCES VERSION(version_id) 
        ON DELETE CASCADE,
    FOREIGN KEY(required_package_id) REFERENCES PACKAGE(package_id) 
        ON DELETE CASCADE
);

CREATE TABLE CONFLICT_PAIR (
    version_id_1 INTEGER NOT NULL,
    version_id_2 INTEGER NOT NULL,
    reason VARCHAR(255),
    PRIMARY KEY (version_id_1, version_id_2),
    FOREIGN KEY (version_id_1) REFERENCES VERSION(version_id) ON DELETE CASCADE,
    FOREIGN KEY (version_id_2) REFERENCES VERSION(version_id) ON DELETE CASCADE,
    -- Ensure version_id_1 < version_id_2 to avoid duplicate representations of the same pair 
    CHECK (version_id_1 < version_id_2)
);

CREATE TABLE INSTALL_AUDIT_LOG (
    audit_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    env_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);