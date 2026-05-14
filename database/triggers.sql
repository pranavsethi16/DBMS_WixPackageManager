USE wix_test;
DROP TRIGGER IF EXISTS ensure_dependencies_met;
DROP TRIGGER IF EXISTS prevent_conflicts;

DELIMITER //

-- 1. Conflict Prevention
DROP TRIGGER IF EXISTS prevent_conflicts //
CREATE TRIGGER prevent_conflicts
BEFORE INSERT ON ENVIRONMENT_PACKAGE
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1
        FROM ENVIRONMENT_PACKAGE EP
        JOIN CONFLICT_PAIR CP ON 
            (CP.version_id_1 = NEW.version_id AND CP.version_id_2 = EP.version_id) OR
            (CP.version_id_2 = NEW.version_id AND CP.version_id_1 = EP.version_id)
        WHERE EP.env_id = NEW.env_id
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Constraint Failed: This version conflicts with an existing package.';
    END IF;
END //

-- 2. Prevent Self-Dependency
DROP TRIGGER IF EXISTS prevent_self_dependency //
CREATE TRIGGER prevent_self_dependency
BEFORE INSERT ON DEPENDENCY
FOR EACH ROW
BEGIN
    DECLARE target_pkg_id INT;
    SELECT package_id INTO target_pkg_id 
    FROM VERSION 
    WHERE version_id = NEW.dependent_version_id;
    
    IF target_pkg_id = NEW.required_package_id THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Constraint Failed: A package version cannot depend on its own base package.';
    END IF;
END //

-- 4. Audit Installation
DROP TRIGGER IF EXISTS log_package_install //
CREATE TRIGGER log_package_install
AFTER INSERT ON ENVIRONMENT_PACKAGE
FOR EACH ROW
BEGIN
    INSERT INTO INSTALL_AUDIT_LOG (env_id, version_id, action) 
    VALUES (NEW.env_id, NEW.version_id, 'INSTALLED');
END //

-- 5. Audit Removal
DROP TRIGGER IF EXISTS log_package_removal //
CREATE TRIGGER log_package_removal
AFTER DELETE ON ENVIRONMENT_PACKAGE
FOR EACH ROW
BEGIN
    INSERT INTO INSTALL_AUDIT_LOG (env_id, version_id, action) 
    VALUES (OLD.env_id, OLD.version_id, 'REMOVED');
END //

DELIMITER ;

SHOW TRIGGERS;