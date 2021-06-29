CREATE TABLE guilds
(id BIGINT PRIMARY KEY, mod_roles BIGINT[], admin_roles BIGINT[],
ticket_category BIGINT, ticket_log_channel BIGINT, support_roles BIGINT[],
ticket_ban_role BIGINT, ticket_index INT, chain_break_role BIGINT,
private_commands BOOLEAN, force_slash BOOLEAN, incident_index INT DEFAULT 1,
mute_role BIGINT, mute_threshold INT DEFAULT 0, ban_threshold INT DEFAULT 0,
bad_words TEXT[] DEFAULT '{}', bad_words_warn_duration BIGINT DEFAULT 0);

CREATE TABLE users
(id BIGINT PRIMARY KEY, trusted BOOLEAN, dad_mode BOOLEAN, mc_uuid TEXT);

CREATE TABLE channels
(id BIGINT PRIMARY KEY, guild_id BIGINT, chain TEXT,
chain_length INTEGER, log_type TEXT, last_chain BIGINT);

CREATE TABLE rules
(name TEXT, guild_id BIGINT, punishment TEXT, description TEXT);

CREATE TABLE incidents
(guild BIGINT, id INT, moderator BIGINT, users BIGINT[], comment TEXT, expires BIGINT, type_ INT, time_ BIGINT, active BOOLEAN, ref TEXT);

CREATE TABLE mutes
(guild BIGINT, member BIGINT, incidents JSON[] DEFAULT '{}', threshold_muted BOOLEAN DEFAULT FALSE, perm_incidents INT[] DEFAULT '{}');
ALTER TABLE mutes ADD CONSTRAINT mutes_pkey PRIMARY KEY (guild, member)
