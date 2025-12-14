-- ===================================
-- RAGFlow-Plus 数据库初始化脚本
-- ===================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `rag_flow` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `rag_flow`;

-- 注意：RAGFlow 会自动创建表结构，此脚本仅用于初始化数据库
-- 如果需要手动创建表，可以从运行中的系统导出表结构

-- 示例：创建初始管理员用户（可选）
-- INSERT INTO `user` (id, nickname, email, password, status, is_superuser, create_time, update_time)
-- VALUES (
--     UUID(),
--     'admin',
--     'admin@example.com',
--     -- 密码: admin123 (经过加密)
--     '$2b$12$your_encrypted_password_here',
--     '1',
--     1,
--     NOW(),
--     NOW()
-- );

-- ===================================
-- 后续如需添加初始数据，在此处添加
-- ===================================
