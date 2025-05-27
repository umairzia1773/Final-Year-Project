-- Create sequences
CREATE SEQUENCE IF NOT EXISTS users_id_seq;
CREATE SEQUENCE IF NOT EXISTS chat_sessions_id_seq;
CREATE SEQUENCE IF NOT EXISTS chat_history_id_seq;

-- Create users table
CREATE TABLE IF NOT EXISTS public.users
(
    id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
    full_name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_email_key UNIQUE (email)
);

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS public.chat_sessions
(
    session_id integer NOT NULL DEFAULT nextval('chat_sessions_id_seq'::regclass),
    user_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    title text,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chat_sessions_pkey PRIMARY KEY (session_id),
    CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);

-- Create chat_history table
CREATE TABLE IF NOT EXISTS public.chat_history
(
    message_id integer NOT NULL DEFAULT nextval('chat_history_id_seq'::regclass),
    user_id integer,
    message text NOT NULL,
    sender character varying(10),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    session_id integer,
    chat_session_id integer,
    CONSTRAINT chat_history_pkey PRIMARY KEY (message_id),
    CONSTRAINT chat_history_chat_session_id_fkey FOREIGN KEY (chat_session_id)
        REFERENCES public.chat_sessions (session_id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT chat_history_session_id_fkey FOREIGN KEY (session_id)
        REFERENCES public.chat_sessions (session_id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT chat_history_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_chat_session FOREIGN KEY (chat_session_id)
        REFERENCES public.chat_sessions (session_id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT chat_history_sender_check CHECK (sender::text = ANY (ARRAY['user'::character varying, 'bot'::character varying]::text[]))
); 