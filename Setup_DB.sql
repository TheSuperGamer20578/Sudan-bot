CREATE TABLE guilds
(id BIGINT PRIMARY KEY, mod_roles BIGINT[], admin_roles BIGINT[],
ticket_category BIGINT, ticket_log_channel BIGINT, support_roles BIGINT[],
ticket_ban_role BIGINT, ticket_index INT, chain_break_role BIGINT);

CREATE TABLE users
(id BIGINT PRIMARY KEY, trusted BOOLEAN, dad_mode BOOLEAN, mc_uuid TEXT);

CREATE TABLE channels
(id BIGINT PRIMARY KEY, guild_id BIGINT, chain TEXT,
chain_length INTEGER, log_type TEXT, last_chain BIGINT);

CREATE TABLE rules
(name TEXT, guild_id BIGINT, punishment TEXT, description TEXT)
