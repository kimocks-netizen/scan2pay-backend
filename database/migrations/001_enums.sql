-- 001_enums.sql
-- Run first — all other migrations depend on these types.

CREATE TYPE user_type        AS ENUM ('vendor', 'tip', 'taxi');
CREATE TYPE user_status      AS ENUM ('active', 'suspended');
CREATE TYPE code_mode        AS ENUM ('fixed', 'amount', 'variable');
CREATE TYPE txn_status       AS ENUM ('pending', 'success', 'failed');
CREATE TYPE payment_method   AS ENUM ('card', 'apple_pay', 'google_pay');
CREATE TYPE settlement_state AS ENUM ('pending', 'settled', 'failed');
CREATE TYPE payout_status    AS ENUM ('pending', 'processing', 'paid', 'failed');
CREATE TYPE merchant_status  AS ENUM ('active', 'suspended', 'closed');
CREATE TYPE pricing_status   AS ENUM ('published', 'scheduled', 'retired');
CREATE TYPE fee_bearer       AS ENUM ('merchant', 'customer', 'split');
