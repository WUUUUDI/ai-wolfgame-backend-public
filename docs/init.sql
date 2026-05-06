create database ai-wolfgame;
use ai-wolfgame

-- 用户表
CREATE TABLE `users` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名',
    `email` VARCHAR(100) NOT NULL COMMENT '邮箱',
    `hashed_password` VARCHAR(255) NOT NULL COMMENT '哈希密码',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用（1启用 0禁用）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 刷新令牌表（存储 Refresh Token 的哈希值）
CREATE TABLE `refresh_tokens` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `token_hash` VARCHAR(255) NOT NULL COMMENT 'Refresh Token 的哈希值（SHA256等）',
    `expires_at` DATETIME NOT NULL COMMENT '过期时间',
    `revoked` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已撤销（1已撤销）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_token_hash` (`token_hash`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Refresh Token 表';