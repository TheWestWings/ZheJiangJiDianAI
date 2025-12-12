-- 角色管理系统数据库表创建脚本
-- 在 MySQL 数据库 rag_flow 中执行

-- 角色表
CREATE TABLE IF NOT EXISTS `role` (
    `id` VARCHAR(32) PRIMARY KEY,
    `name` VARCHAR(64) NOT NULL UNIQUE,
    `description` TEXT,
    `is_default` INT DEFAULT 0,
    `status` CHAR(1) DEFAULT '1',
    `create_time` BIGINT,
    `update_time` BIGINT,
    `create_date` DATETIME,
    `update_date` DATETIME,
    INDEX `idx_role_name` (`name`),
    INDEX `idx_role_is_default` (`is_default`),
    INDEX `idx_role_status` (`status`),
    INDEX `idx_role_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS `user_role` (
    `id` VARCHAR(32) PRIMARY KEY,
    `user_id` VARCHAR(32) NOT NULL,
    `role_id` VARCHAR(32) NOT NULL,
    `create_time` BIGINT,
    `update_time` BIGINT,
    `create_date` DATETIME,
    `update_date` DATETIME,
    INDEX `idx_user_role_user_id` (`user_id`),
    INDEX `idx_user_role_role_id` (`role_id`),
    UNIQUE KEY `uk_user_role` (`user_id`, `role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 知识库角色权限表
CREATE TABLE IF NOT EXISTS `knowledgebase_role` (
    `id` VARCHAR(32) PRIMARY KEY,
    `kb_id` VARCHAR(32) NOT NULL,
    `role_id` VARCHAR(32) NOT NULL,
    `create_time` BIGINT,
    `update_time` BIGINT,
    `create_date` DATETIME,
    `update_date` DATETIME,
    INDEX `idx_kb_role_kb_id` (`kb_id`),
    INDEX `idx_kb_role_role_id` (`role_id`),
    UNIQUE KEY `uk_kb_role` (`kb_id`, `role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 模型角色权限表
CREATE TABLE IF NOT EXISTS `model_role` (
    `id` VARCHAR(32) PRIMARY KEY,
    `tenant_id` VARCHAR(32) NOT NULL,
    `llm_factory` VARCHAR(128) NOT NULL,
    `llm_name` VARCHAR(128) NOT NULL,
    `role_id` VARCHAR(32) NOT NULL,
    `create_time` BIGINT,
    `update_time` BIGINT,
    `create_date` DATETIME,
    `update_date` DATETIME,
    INDEX `idx_model_role_tenant_id` (`tenant_id`),
    INDEX `idx_model_role_role_id` (`role_id`),
    UNIQUE KEY `uk_model_role` (`tenant_id`, `llm_factory`, `llm_name`, `role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
