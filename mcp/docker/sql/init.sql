--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Debian 17.5-1.pgdg120+1)
-- Dumped by pg_dump version 17.5 (Debian 17.5-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: availability; Type: TABLE; Schema: public; Owner: aip_user
--

CREATE EXTENSION vector WITH SCHEMA public;


CREATE TABLE public.availability (
    role text,
    provider_name text,
    is_available boolean,
    patient_to_attend text,
    dt_time_slot timestamp without time zone
);


ALTER TABLE public.availability OWNER TO aip_user;

--
-- Data for Name: availability; Type: TABLE DATA; Schema: public; Owner: aip_user
--

COPY public.availability (role, provider_name, is_available, patient_to_attend, dt_time_slot) FROM stdin;
Pharmacist	michael green	t	\N	2024-08-19 12:00:00
Pharmacist	michael green	t	\N	2024-08-19 12:30:00
Pharmacist	michael green	t	\N	2024-08-19 13:00:00
Pharmacist	michael green	t	\N	2024-08-19 13:30:00
Pharmacist	michael green	f	1000060.0	2024-08-19 14:00:00
Pharmacist	michael green	t	\N	2024-08-19 14:30:00
Pharmacist	michael green	f	1000073.0	2024-08-19 15:00:00
Pharmacist	michael green	t	\N	2024-08-19 15:30:00
Pharmacist	michael green	t	\N	2024-08-19 16:00:00
Pharmacist	michael green	f	1000004.0	2024-08-19 16:30:00
Pharmacist	michael green	f	1000037.0	2024-08-20 08:00:00
Pharmacist	michael green	t	\N	2024-08-20 08:30:00
Pharmacist	michael green	t	\N	2024-08-20 09:00:00
Pharmacist	michael green	f	1000047.0	2024-08-20 09:30:00
Pharmacist	michael green	f	1000036.0	2024-08-20 10:00:00
Pharmacist	michael green	t	\N	2024-08-20 10:30:00
Pharmacist	michael green	t	\N	2024-08-20 11:00:00
Pharmacist	michael green	t	\N	2024-08-20 11:30:00
Pharmacist	michael green	t	\N	2024-08-20 12:00:00
Pharmacist	michael green	t	\N	2024-08-20 12:30:00
Pharmacist	michael green	f	1000042.0	2024-08-20 13:00:00
Pharmacist	michael green	t	\N	2024-08-20 13:30:00
Pharmacist	michael green	t	\N	2024-08-20 14:00:00
Pharmacist	michael green	t	\N	2024-08-20 14:30:00
Pharmacist	michael green	t	\N	2024-08-20 15:00:00
Pharmacist	michael green	t	\N	2024-08-20 15:30:00
Pharmacist	michael green	t	\N	2024-08-20 16:00:00
Pharmacist	michael green	t	\N	2024-08-20 16:30:00
Pharmacist	michael green	t	\N	2024-08-21 08:00:00
Pharmacist	michael green	t	\N	2024-08-21 08:30:00
Pharmacist	michael green	t	\N	2024-08-21 09:00:00
Pharmacist	michael green	t	\N	2024-08-21 09:30:00
Pharmacist	michael green	f	1000089.0	2024-08-21 10:00:00
Pharmacist	michael green	t	\N	2024-08-21 10:30:00
Pharmacist	michael green	f	1000099.0	2024-08-21 11:00:00
Occupational Therapist	lisa brown	f	1000056.0	2024-08-06 14:00:00
Occupational Therapist	lisa brown	f	1000099.0	2024-08-06 14:30:00
Occupational Therapist	lisa brown	f	1000048.0	2024-08-06 15:00:00
Occupational Therapist	lisa brown	f	1000004.0	2024-08-06 15:30:00
Occupational Therapist	lisa brown	f	1000006.0	2024-08-06 16:00:00
Occupational Therapist	lisa brown	f	1000016.0	2024-08-06 16:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 08:30:00
Occupational Therapist	lisa brown	f	1000085.0	2024-08-07 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 09:30:00
Occupational Therapist	lisa brown	f	1000082.0	2024-08-07 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 11:30:00
Occupational Therapist	lisa brown	f	1000013.0	2024-08-07 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 15:30:00
Home Health Aide	sarah wilson	f	1000050.0	2024-08-05 08:00:00
Home Health Aide	sarah wilson	f	1000028.0	2024-08-05 08:30:00
Home Health Aide	sarah wilson	f	1000035.0	2024-08-05 09:00:00
Home Health Aide	sarah wilson	f	1000065.0	2024-08-05 09:30:00
Home Health Aide	sarah wilson	f	1000031.0	2024-08-05 10:00:00
Home Health Aide	sarah wilson	f	1000087.0	2024-08-05 10:30:00
Home Health Aide	sarah wilson	f	1000077.0	2024-08-05 11:00:00
Home Health Aide	sarah wilson	f	1000059.0	2024-08-05 11:30:00
Home Health Aide	sarah wilson	f	1000081.0	2024-08-05 12:00:00
Home Health Aide	sarah wilson	f	1000010.0	2024-08-05 12:30:00
Home Health Aide	sarah wilson	f	1000084.0	2024-08-05 13:00:00
Home Health Aide	sarah wilson	f	1000000.0	2024-08-05 13:30:00
Home Health Aide	sarah wilson	f	1000069.0	2024-08-05 14:00:00
Home Health Aide	sarah wilson	f	1000096.0	2024-08-05 14:30:00
Home Health Aide	sarah wilson	f	1000078.0	2024-08-05 15:00:00
Home Health Aide	sarah wilson	f	1000035.0	2024-08-05 15:30:00
Home Health Aide	sarah wilson	f	1000064.0	2024-08-05 16:00:00
Home Health Aide	sarah wilson	f	1000064.0	2024-08-05 16:30:00
Home Health Aide	sarah wilson	f	1000086.0	2024-08-06 08:00:00
Home Health Aide	sarah wilson	f	1000062.0	2024-08-06 08:30:00
Home Health Aide	sarah wilson	f	1000029.0	2024-08-06 09:00:00
Home Health Aide	sarah wilson	f	1000002.0	2024-08-06 09:30:00
Home Health Aide	sarah wilson	f	1000021.0	2024-08-06 10:00:00
Home Health Aide	sarah wilson	f	1000055.0	2024-08-06 10:30:00
Home Health Aide	sarah wilson	f	1000093.0	2024-08-06 11:00:00
Home Health Aide	sarah wilson	f	1000085.0	2024-08-06 11:30:00
Home Health Aide	sarah wilson	f	1000041.0	2024-08-06 12:00:00
Home Health Aide	sarah wilson	f	1000093.0	2024-08-06 12:30:00
Home Health Aide	sarah wilson	f	1000085.0	2024-08-06 13:00:00
Home Health Aide	sarah wilson	f	1000063.0	2024-08-06 13:30:00
Home Health Aide	sarah wilson	f	1000032.0	2024-08-06 14:00:00
Home Health Aide	sarah wilson	f	1000039.0	2024-08-06 14:30:00
Home Health Aide	sarah wilson	f	1000056.0	2024-08-06 15:00:00
Home Health Aide	sarah wilson	f	1000050.0	2024-08-06 15:30:00
Home Health Aide	sarah wilson	f	1000011.0	2024-08-06 16:00:00
Home Health Aide	sarah wilson	f	1000003.0	2024-08-06 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 08:00:00
Home Health Aide	sarah wilson	f	1000096.0	2024-08-07 08:30:00
Home Health Aide	sarah wilson	f	1000024.0	2024-08-07 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 10:00:00
Home Health Aide	sarah wilson	f	1000019.0	2024-08-07 10:30:00
Home Health Aide	sarah wilson	f	1000001.0	2024-08-07 11:00:00
Home Health Aide	sarah wilson	f	1000035.0	2024-08-07 11:30:00
Home Health Aide	sarah wilson	f	1000097.0	2024-08-07 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 14:30:00
Home Health Aide	sarah wilson	f	1000077.0	2024-08-07 15:00:00
Home Health Aide	sarah wilson	f	1000055.0	2024-08-07 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-07 16:30:00
Home Health Aide	sarah wilson	f	1000019.0	2024-08-08 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-08 08:30:00
Home Health Aide	sarah wilson	f	1000018.0	2024-08-08 09:00:00
Home Health Aide	sarah wilson	f	1000028.0	2024-08-08 09:30:00
Home Health Aide	sarah wilson	f	1000064.0	2024-08-08 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-08 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-08 11:00:00
Home Health Aide	sarah wilson	f	1000005.0	2024-08-08 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-08 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-08 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-08 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-08 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-08 14:00:00
Home Health Aide	sarah wilson	f	1000059.0	2024-08-08 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-08 15:00:00
Home Health Aide	sarah wilson	f	1000058.0	2024-08-08 15:30:00
Home Health Aide	sarah wilson	f	1000094.0	2024-08-08 16:00:00
Home Health Aide	sarah wilson	f	1000004.0	2024-08-08 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 08:00:00
Home Health Aide	sarah wilson	f	1000034.0	2024-08-09 08:30:00
Home Health Aide	sarah wilson	f	1000022.0	2024-08-09 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 10:00:00
Home Health Aide	sarah wilson	f	1000049.0	2024-08-09 10:30:00
Home Health Aide	sarah wilson	f	1000100.0	2024-08-09 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 11:30:00
Home Health Aide	sarah wilson	f	1000097.0	2024-08-09 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 13:00:00
Home Health Aide	sarah wilson	f	1000001.0	2024-08-09 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-09 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-10 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-10 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-10 10:00:00
Home Health Aide	sarah wilson	f	1000080.0	2024-08-10 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-10 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-10 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-10 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-10 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 09:30:00
Home Health Aide	sarah wilson	f	1000075.0	2024-08-12 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 11:30:00
Home Health Aide	sarah wilson	f	1000017.0	2024-08-12 12:00:00
Home Health Aide	sarah wilson	f	1000003.0	2024-08-12 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 13:00:00
Home Health Aide	sarah wilson	f	1000042.0	2024-08-12 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 14:00:00
Home Health Aide	sarah wilson	f	1000078.0	2024-08-12 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-12 16:30:00
Home Health Aide	sarah wilson	f	1000074.0	2024-08-13 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 10:30:00
Home Health Aide	sarah wilson	f	1000014.0	2024-08-13 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 11:30:00
Home Health Aide	sarah wilson	f	1000071.0	2024-08-13 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 12:30:00
Home Health Aide	sarah wilson	f	1000025.0	2024-08-13 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 15:00:00
Home Health Aide	sarah wilson	f	1000074.0	2024-08-13 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-13 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 08:00:00
Home Health Aide	sarah wilson	f	1000026.0	2024-08-14 08:30:00
Home Health Aide	sarah wilson	f	1000097.0	2024-08-14 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 11:30:00
Home Health Aide	sarah wilson	f	1000045.0	2024-08-14 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 15:00:00
Home Health Aide	sarah wilson	f	1000011.0	2024-08-14 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-14 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 09:00:00
Home Health Aide	sarah wilson	f	1000071.0	2024-08-15 09:30:00
Home Health Aide	sarah wilson	f	1000067.0	2024-08-15 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 14:00:00
Home Health Aide	sarah wilson	f	1000006.0	2024-08-15 14:30:00
Home Health Aide	sarah wilson	f	1000078.0	2024-08-15 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 15:30:00
Home Health Aide	sarah wilson	f	1000083.0	2024-08-15 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-15 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 09:00:00
Home Health Aide	sarah wilson	f	1000004.0	2024-08-16 09:30:00
Home Health Aide	sarah wilson	f	1000048.0	2024-08-16 10:00:00
Home Health Aide	sarah wilson	f	1000061.0	2024-08-16 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 13:30:00
Home Health Aide	sarah wilson	f	1000046.0	2024-08-16 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-16 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-17 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-17 09:30:00
Home Health Aide	sarah wilson	f	1000017.0	2024-08-17 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-17 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-17 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-17 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-17 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-17 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 10:30:00
Home Health Aide	sarah wilson	f	1000066.0	2024-08-19 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 12:30:00
Home Health Aide	sarah wilson	f	1000073.0	2024-08-19 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 14:00:00
Home Health Aide	sarah wilson	f	1000028.0	2024-08-19 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 15:30:00
Home Health Aide	sarah wilson	f	1000090.0	2024-08-19 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-19 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 12:00:00
Home Health Aide	sarah wilson	f	1000042.0	2024-08-20 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 13:30:00
Home Health Aide	sarah wilson	f	1000067.0	2024-08-20 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 15:00:00
Home Health Aide	sarah wilson	f	1000023.0	2024-08-20 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-20 16:00:00
Home Health Aide	sarah wilson	f	1000085.0	2024-08-20 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 08:00:00
Home Health Aide	sarah wilson	f	1000037.0	2024-08-21 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 09:00:00
Home Health Aide	sarah wilson	f	1000026.0	2024-08-21 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 10:00:00
Home Health Aide	sarah wilson	f	1000052.0	2024-08-21 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 11:00:00
Home Health Aide	sarah wilson	f	1000023.0	2024-08-21 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 13:00:00
Home Health Aide	sarah wilson	f	1000005.0	2024-08-21 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 14:30:00
Home Health Aide	sarah wilson	f	1000036.0	2024-08-21 15:00:00
Home Health Aide	sarah wilson	f	1000078.0	2024-08-21 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-21 16:00:00
Home Health Aide	sarah wilson	f	1000075.0	2024-08-21 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 09:00:00
Home Health Aide	sarah wilson	f	1000071.0	2024-08-22 09:30:00
Home Health Aide	sarah wilson	f	1000095.0	2024-08-22 10:00:00
Home Health Aide	sarah wilson	f	1000007.0	2024-08-22 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 12:00:00
Home Health Aide	sarah wilson	f	1000017.0	2024-08-22 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 13:00:00
Home Health Aide	sarah wilson	f	1000081.0	2024-08-22 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 14:30:00
Home Health Aide	sarah wilson	f	1000068.0	2024-08-22 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-22 16:00:00
Home Health Aide	sarah wilson	f	1000079.0	2024-08-22 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 08:30:00
Home Health Aide	sarah wilson	f	1000008.0	2024-08-23 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 11:00:00
Home Health Aide	sarah wilson	f	1000041.0	2024-08-23 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 13:00:00
Home Health Aide	sarah wilson	f	1000032.0	2024-08-23 13:30:00
Home Health Aide	sarah wilson	f	1000013.0	2024-08-23 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 15:00:00
Home Health Aide	sarah wilson	f	1000066.0	2024-08-23 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-23 16:30:00
Home Health Aide	sarah wilson	f	1000011.0	2024-08-24 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-24 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-24 10:00:00
Home Health Aide	sarah wilson	f	1000048.0	2024-08-24 10:30:00
Home Health Aide	sarah wilson	f	1000004.0	2024-08-24 11:00:00
Home Health Aide	sarah wilson	f	1000013.0	2024-08-24 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-24 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-24 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 08:00:00
Home Health Aide	sarah wilson	f	1000071.0	2024-08-26 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 10:30:00
Home Health Aide	sarah wilson	f	1000007.0	2024-08-26 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 11:30:00
Home Health Aide	sarah wilson	f	1000052.0	2024-08-26 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 15:00:00
Home Health Aide	sarah wilson	f	1000050.0	2024-08-26 15:30:00
Home Health Aide	sarah wilson	f	1000067.0	2024-08-26 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-26 16:30:00
Home Health Aide	sarah wilson	f	1000023.0	2024-08-27 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 09:00:00
Home Health Aide	sarah wilson	f	1000080.0	2024-08-27 09:30:00
Home Health Aide	sarah wilson	f	1000036.0	2024-08-27 10:00:00
Home Health Aide	sarah wilson	f	1000034.0	2024-08-27 10:30:00
Home Health Aide	sarah wilson	f	1000051.0	2024-08-27 11:00:00
Home Health Aide	sarah wilson	f	1000020.0	2024-08-27 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-27 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 08:30:00
Home Health Aide	sarah wilson	f	1000029.0	2024-08-28 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 10:00:00
Home Health Aide	sarah wilson	f	1000070.0	2024-08-28 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 12:00:00
Home Health Aide	sarah wilson	f	1000006.0	2024-08-28 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 15:00:00
Home Health Aide	sarah wilson	f	1000076.0	2024-08-28 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-28 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 10:00:00
Home Health Aide	sarah wilson	f	1000013.0	2024-08-29 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 11:30:00
Home Health Aide	sarah wilson	f	1000053.0	2024-08-29 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 13:00:00
Home Health Aide	sarah wilson	f	1000059.0	2024-08-29 13:30:00
Home Health Aide	sarah wilson	f	1000090.0	2024-08-29 14:00:00
Home Health Aide	sarah wilson	f	1000075.0	2024-08-29 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-29 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 08:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 10:00:00
Home Health Aide	sarah wilson	f	1000033.0	2024-08-30 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 13:00:00
Home Health Aide	sarah wilson	f	1000058.0	2024-08-30 13:30:00
Home Health Aide	sarah wilson	f	1000000.0	2024-08-30 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-30 16:30:00
Home Health Aide	sarah wilson	f	1000000.0	2024-08-31 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-31 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-31 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-31 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-31 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-31 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-08-31 12:00:00
Home Health Aide	sarah wilson	t	\N	2024-08-31 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 08:30:00
Home Health Aide	sarah wilson	f	1000028.0	2024-09-02 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 10:00:00
Home Health Aide	sarah wilson	f	1000003.0	2024-09-02 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 12:00:00
Home Health Aide	sarah wilson	f	1000059.0	2024-09-02 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 13:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 13:30:00
Home Health Aide	sarah wilson	f	1000077.0	2024-09-02 14:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 14:30:00
Home Health Aide	sarah wilson	f	1000005.0	2024-09-02 15:00:00
Home Health Aide	sarah wilson	f	1000059.0	2024-09-02 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-02 16:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 08:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 08:30:00
Home Health Aide	sarah wilson	f	1000057.0	2024-09-03 09:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 09:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 10:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 10:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 11:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 11:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 12:00:00
Home Health Aide	sarah wilson	f	1000028.0	2024-09-03 12:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 13:00:00
Home Health Aide	sarah wilson	f	1000005.0	2024-09-03 13:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 14:00:00
Home Health Aide	sarah wilson	f	1000015.0	2024-09-03 14:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 15:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 15:30:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 16:00:00
Home Health Aide	sarah wilson	t	\N	2024-09-03 16:30:00
Care Coordinator	robert martinez	f	1000045.0	2024-08-05 08:00:00
Care Coordinator	robert martinez	f	1000100.0	2024-08-05 08:30:00
Care Coordinator	robert martinez	f	1000043.0	2024-08-05 09:00:00
Care Coordinator	robert martinez	f	1000029.0	2024-08-05 09:30:00
Care Coordinator	robert martinez	f	1000069.0	2024-08-05 10:00:00
Care Coordinator	robert martinez	f	1000098.0	2024-08-05 10:30:00
Care Coordinator	robert martinez	f	1000017.0	2024-08-05 11:00:00
Care Coordinator	robert martinez	f	1000020.0	2024-08-05 11:30:00
Care Coordinator	robert martinez	f	1000046.0	2024-08-05 12:00:00
Care Coordinator	robert martinez	f	1000084.0	2024-08-05 12:30:00
Care Coordinator	robert martinez	f	1000046.0	2024-08-05 13:00:00
Care Coordinator	robert martinez	f	1000031.0	2024-08-05 13:30:00
Care Coordinator	robert martinez	f	1000075.0	2024-08-05 14:00:00
Care Coordinator	robert martinez	f	1000068.0	2024-08-05 14:30:00
Care Coordinator	robert martinez	f	1000072.0	2024-08-05 15:00:00
Care Coordinator	robert martinez	f	1000095.0	2024-08-05 15:30:00
Care Coordinator	robert martinez	f	1000006.0	2024-08-05 16:00:00
Care Coordinator	robert martinez	f	1000019.0	2024-08-05 16:30:00
Care Coordinator	robert martinez	f	1000000.0	2024-08-06 08:00:00
Care Coordinator	robert martinez	f	1000038.0	2024-08-06 08:30:00
Care Coordinator	robert martinez	f	1000016.0	2024-08-06 09:00:00
Care Coordinator	robert martinez	f	1000043.0	2024-08-06 09:30:00
Care Coordinator	robert martinez	f	1000078.0	2024-08-06 10:00:00
Care Coordinator	robert martinez	f	1000054.0	2024-08-06 10:30:00
Care Coordinator	robert martinez	f	1000068.0	2024-08-06 11:00:00
Care Coordinator	robert martinez	f	1000058.0	2024-08-06 11:30:00
Care Coordinator	robert martinez	f	1000037.0	2024-08-06 12:00:00
Care Coordinator	robert martinez	f	1000053.0	2024-08-06 12:30:00
Care Coordinator	robert martinez	f	1000081.0	2024-08-06 13:00:00
Care Coordinator	robert martinez	f	1000020.0	2024-08-06 13:30:00
Care Coordinator	robert martinez	f	1000025.0	2024-08-06 14:00:00
Care Coordinator	robert martinez	f	1000053.0	2024-08-06 14:30:00
Care Coordinator	robert martinez	f	1000053.0	2024-08-06 15:00:00
Care Coordinator	robert martinez	f	1000087.0	2024-08-06 15:30:00
Care Coordinator	robert martinez	f	1000069.0	2024-08-06 16:00:00
Care Coordinator	robert martinez	f	1000044.0	2024-08-06 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-07 08:00:00
Care Coordinator	robert martinez	f	1000051.0	2024-08-07 08:30:00
Care Coordinator	robert martinez	f	1000063.0	2024-08-07 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-07 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-07 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-07 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-07 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-07 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-07 12:00:00
Care Coordinator	robert martinez	f	1000099.0	2024-08-07 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-07 13:00:00
Social Worker	emily johnson	f	1000082.0	2024-08-05 08:00:00
Social Worker	emily johnson	f	1000070.0	2024-08-05 08:30:00
Social Worker	emily johnson	f	1000015.0	2024-08-05 09:00:00
Social Worker	emily johnson	f	1000039.0	2024-08-05 09:30:00
Social Worker	emily johnson	f	1000060.0	2024-08-05 10:00:00
Social Worker	emily johnson	f	1000050.0	2024-08-05 10:30:00
Social Worker	emily johnson	f	1000011.0	2024-08-05 11:00:00
Social Worker	emily johnson	f	1000052.0	2024-08-05 11:30:00
Social Worker	emily johnson	f	1000098.0	2024-08-05 12:00:00
Social Worker	emily johnson	f	1000013.0	2024-08-05 12:30:00
Social Worker	emily johnson	f	1000063.0	2024-08-05 13:00:00
Social Worker	emily johnson	f	1000067.0	2024-08-05 13:30:00
Social Worker	emily johnson	f	1000068.0	2024-08-05 14:00:00
Social Worker	emily johnson	f	1000100.0	2024-08-05 14:30:00
Social Worker	emily johnson	f	1000063.0	2024-08-05 15:00:00
Social Worker	emily johnson	f	1000099.0	2024-08-05 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-07 13:30:00
Care Coordinator	robert martinez	f	1000084.0	2024-08-07 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-07 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-07 15:00:00
Care Coordinator	robert martinez	t	\N	2024-08-07 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-07 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-07 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-08 08:00:00
Care Coordinator	robert martinez	f	1000081.0	2024-08-08 08:30:00
Care Coordinator	robert martinez	t	\N	2024-08-08 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-08 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-08 10:00:00
Care Coordinator	robert martinez	f	1000092.0	2024-08-08 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-08 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-08 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-08 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-08 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-08 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-08 13:30:00
Care Coordinator	robert martinez	f	1000025.0	2024-08-08 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-08 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-08 15:00:00
Care Coordinator	robert martinez	f	1000019.0	2024-08-08 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-08 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-08 16:30:00
Care Coordinator	robert martinez	f	1000028.0	2024-08-09 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-09 08:30:00
Care Coordinator	robert martinez	f	1000083.0	2024-08-09 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-09 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-09 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-09 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-09 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-09 11:30:00
Care Coordinator	robert martinez	f	1000051.0	2024-08-09 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-09 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-09 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-09 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-09 14:00:00
Care Coordinator	robert martinez	f	1000032.0	2024-08-09 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-09 15:00:00
Care Coordinator	robert martinez	t	\N	2024-08-09 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-09 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-09 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-10 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-10 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-10 10:00:00
Care Coordinator	robert martinez	f	1000078.0	2024-08-10 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-10 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-10 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-10 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-10 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-12 08:00:00
Care Coordinator	robert martinez	f	1000030.0	2024-08-12 08:30:00
Care Coordinator	robert martinez	f	1000093.0	2024-08-12 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-12 09:30:00
Care Coordinator	robert martinez	f	1000098.0	2024-08-12 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-12 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-12 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-12 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-12 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-12 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-12 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-12 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-12 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-12 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-12 15:00:00
Care Coordinator	robert martinez	t	\N	2024-08-12 15:30:00
Care Coordinator	robert martinez	f	1000046.0	2024-08-12 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-12 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-13 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-13 08:30:00
Care Coordinator	robert martinez	f	1000039.0	2024-08-13 09:00:00
Care Coordinator	robert martinez	f	1000092.0	2024-08-13 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-13 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-13 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-13 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-13 11:30:00
Care Coordinator	robert martinez	f	1000062.0	2024-08-13 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-13 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-13 13:00:00
Care Coordinator	robert martinez	f	1000092.0	2024-08-13 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-13 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-13 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-13 15:00:00
Care Coordinator	robert martinez	f	1000092.0	2024-08-13 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-13 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-13 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-14 08:00:00
Care Coordinator	robert martinez	f	1000099.0	2024-08-14 08:30:00
Care Coordinator	robert martinez	t	\N	2024-08-14 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-14 09:30:00
Care Coordinator	robert martinez	f	1000059.0	2024-08-14 10:00:00
Care Coordinator	robert martinez	f	1000076.0	2024-08-14 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-14 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-14 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-14 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-14 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-14 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-14 13:30:00
Care Coordinator	robert martinez	f	1000085.0	2024-08-14 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-14 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-14 15:00:00
Care Coordinator	robert martinez	f	1000009.0	2024-08-14 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-14 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-14 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-15 08:00:00
Care Coordinator	robert martinez	f	1000097.0	2024-08-15 08:30:00
Care Coordinator	robert martinez	t	\N	2024-08-15 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-15 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-15 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-15 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-15 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-15 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-15 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-15 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-15 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-15 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-15 14:00:00
Care Coordinator	robert martinez	f	1000072.0	2024-08-15 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-15 15:00:00
Care Coordinator	robert martinez	t	\N	2024-08-15 15:30:00
Care Coordinator	robert martinez	f	1000026.0	2024-08-15 16:00:00
Care Coordinator	robert martinez	f	1000068.0	2024-08-15 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-16 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-16 08:30:00
Care Coordinator	robert martinez	t	\N	2024-08-16 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-16 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-16 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-16 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-16 11:00:00
Care Coordinator	robert martinez	f	1000089.0	2024-08-16 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-16 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-16 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-16 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-16 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-16 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-16 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-16 15:00:00
Care Coordinator	robert martinez	f	1000062.0	2024-08-16 15:30:00
Care Coordinator	robert martinez	f	1000053.0	2024-08-16 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-16 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-17 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-17 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-17 10:00:00
Care Coordinator	robert martinez	f	1000094.0	2024-08-17 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-17 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-17 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-17 12:00:00
Care Coordinator	robert martinez	f	1000046.0	2024-08-17 12:30:00
Care Coordinator	robert martinez	f	1000095.0	2024-08-19 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-19 08:30:00
Care Coordinator	robert martinez	t	\N	2024-08-19 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-19 09:30:00
Care Coordinator	robert martinez	f	1000024.0	2024-08-19 10:00:00
Care Coordinator	robert martinez	f	1000045.0	2024-08-19 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-19 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-19 11:30:00
Care Coordinator	robert martinez	f	1000027.0	2024-08-19 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-19 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-19 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-19 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-19 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-19 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-19 15:00:00
Care Coordinator	robert martinez	t	\N	2024-08-19 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-19 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-19 16:30:00
Care Coordinator	robert martinez	f	1000037.0	2024-08-20 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-20 08:30:00
Care Coordinator	robert martinez	t	\N	2024-08-20 09:00:00
Care Coordinator	robert martinez	f	1000093.0	2024-08-20 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-20 10:00:00
Care Coordinator	robert martinez	f	1000078.0	2024-08-20 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-20 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-20 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-20 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-20 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-20 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-20 13:30:00
Care Coordinator	robert martinez	f	1000055.0	2024-08-20 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-20 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-20 15:00:00
Care Coordinator	robert martinez	t	\N	2024-08-20 15:30:00
Care Coordinator	robert martinez	f	1000004.0	2024-08-20 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-20 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-21 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-21 08:30:00
Care Coordinator	robert martinez	f	1000014.0	2024-08-21 09:00:00
Care Coordinator	robert martinez	f	1000002.0	2024-08-21 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-21 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-21 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-21 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-21 11:30:00
Care Coordinator	robert martinez	f	1000041.0	2024-08-21 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-21 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-21 13:00:00
Care Coordinator	robert martinez	f	1000014.0	2024-08-21 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-21 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-21 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-21 15:00:00
Care Coordinator	robert martinez	t	\N	2024-08-21 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-21 16:00:00
Care Coordinator	robert martinez	f	1000008.0	2024-08-21 16:30:00
Care Coordinator	robert martinez	f	1000041.0	2024-08-22 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-22 08:30:00
Care Coordinator	robert martinez	t	\N	2024-08-22 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-22 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-22 10:00:00
Care Coordinator	robert martinez	f	1000015.0	2024-08-22 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-22 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-22 11:30:00
Care Coordinator	robert martinez	f	1000046.0	2024-08-22 12:00:00
Care Coordinator	robert martinez	f	1000100.0	2024-08-22 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-22 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-22 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-22 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-22 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-22 15:00:00
Care Coordinator	robert martinez	f	1000060.0	2024-08-22 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-22 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-22 16:30:00
Care Coordinator	robert martinez	f	1000048.0	2024-08-23 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-23 08:30:00
Care Coordinator	robert martinez	f	1000073.0	2024-08-23 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-23 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-23 10:00:00
Care Coordinator	robert martinez	f	1000041.0	2024-08-23 10:30:00
Care Coordinator	robert martinez	f	1000075.0	2024-08-23 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-23 11:30:00
Care Coordinator	robert martinez	f	1000044.0	2024-08-23 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-23 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-23 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-23 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-23 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-23 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-23 15:00:00
Care Coordinator	robert martinez	t	\N	2024-08-23 15:30:00
Care Coordinator	robert martinez	f	1000073.0	2024-08-23 16:00:00
Care Coordinator	robert martinez	f	1000010.0	2024-08-23 16:30:00
Care Coordinator	robert martinez	f	1000058.0	2024-08-24 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-24 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-24 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-24 10:30:00
Care Coordinator	robert martinez	f	1000092.0	2024-08-24 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-24 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-24 12:00:00
Care Coordinator	robert martinez	f	1000015.0	2024-08-24 12:30:00
Care Coordinator	robert martinez	f	1000011.0	2024-08-26 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-26 08:30:00
Care Coordinator	robert martinez	t	\N	2024-08-26 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-26 09:30:00
Care Coordinator	robert martinez	f	1000090.0	2024-08-26 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-26 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-26 11:00:00
Care Coordinator	robert martinez	f	1000064.0	2024-08-26 11:30:00
Care Coordinator	robert martinez	f	1000041.0	2024-08-26 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-26 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-26 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-26 13:30:00
Care Coordinator	robert martinez	f	1000034.0	2024-08-26 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-26 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-26 15:00:00
Care Coordinator	robert martinez	f	1000064.0	2024-08-26 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-26 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-26 16:30:00
Care Coordinator	robert martinez	f	1000030.0	2024-08-27 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-27 08:30:00
Care Coordinator	robert martinez	f	1000100.0	2024-08-27 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-27 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-27 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-27 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-27 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-27 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-27 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-27 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-27 13:00:00
Care Coordinator	robert martinez	f	1000058.0	2024-08-27 13:30:00
Care Coordinator	robert martinez	f	1000022.0	2024-08-27 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-27 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-27 15:00:00
Care Coordinator	robert martinez	t	\N	2024-08-27 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-27 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-27 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-28 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-28 08:30:00
Care Coordinator	robert martinez	f	1000038.0	2024-08-28 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-28 09:30:00
Care Coordinator	robert martinez	f	1000001.0	2024-08-28 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-28 10:30:00
Care Coordinator	robert martinez	f	1000021.0	2024-08-28 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-28 11:30:00
Care Coordinator	robert martinez	f	1000036.0	2024-08-28 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-28 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-28 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-28 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-28 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-28 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-28 15:00:00
Care Coordinator	robert martinez	f	1000072.0	2024-08-28 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-28 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-28 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-29 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-29 08:30:00
Care Coordinator	robert martinez	f	1000043.0	2024-08-29 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-29 09:30:00
Care Coordinator	robert martinez	f	1000086.0	2024-08-29 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-29 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-29 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-29 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-29 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-29 12:30:00
Care Coordinator	robert martinez	f	1000099.0	2024-08-29 13:00:00
Care Coordinator	robert martinez	f	1000009.0	2024-08-29 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-29 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-29 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-29 15:00:00
Care Coordinator	robert martinez	f	1000061.0	2024-08-29 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-29 16:00:00
Care Coordinator	robert martinez	f	1000094.0	2024-08-29 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-30 08:00:00
Care Coordinator	robert martinez	t	\N	2024-08-30 08:30:00
Care Coordinator	robert martinez	t	\N	2024-08-30 09:00:00
Care Coordinator	robert martinez	t	\N	2024-08-30 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-30 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-30 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-30 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-30 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-30 12:00:00
Care Coordinator	robert martinez	f	1000008.0	2024-08-30 12:30:00
Care Coordinator	robert martinez	t	\N	2024-08-30 13:00:00
Care Coordinator	robert martinez	t	\N	2024-08-30 13:30:00
Care Coordinator	robert martinez	t	\N	2024-08-30 14:00:00
Care Coordinator	robert martinez	t	\N	2024-08-30 14:30:00
Care Coordinator	robert martinez	t	\N	2024-08-30 15:00:00
Nutritionist	jane smith	f	1000058.0	2024-08-05 08:00:00
Nutritionist	jane smith	f	1000080.0	2024-08-05 08:30:00
Nutritionist	jane smith	f	1000007.0	2024-08-05 09:00:00
Nutritionist	jane smith	f	1000023.0	2024-08-05 09:30:00
Nutritionist	jane smith	f	1000078.0	2024-08-05 10:00:00
Nutritionist	jane smith	f	1000093.0	2024-08-05 10:30:00
Nutritionist	jane smith	f	1000084.0	2024-08-05 11:00:00
Nutritionist	jane smith	f	1000052.0	2024-08-05 11:30:00
Nutritionist	jane smith	f	1000021.0	2024-08-05 12:00:00
Nutritionist	jane smith	f	1000044.0	2024-08-05 12:30:00
Nutritionist	jane smith	f	1000037.0	2024-08-05 13:00:00
Nutritionist	jane smith	f	1000088.0	2024-08-05 13:30:00
Nutritionist	jane smith	f	1000052.0	2024-08-05 14:00:00
Nutritionist	jane smith	f	1000000.0	2024-08-05 14:30:00
Nutritionist	jane smith	f	1000066.0	2024-08-05 15:00:00
Nutritionist	jane smith	f	1000039.0	2024-08-05 15:30:00
Nutritionist	jane smith	f	1000027.0	2024-08-05 16:00:00
Nutritionist	jane smith	f	1000018.0	2024-08-05 16:30:00
Nutritionist	jane smith	f	1000062.0	2024-08-06 08:00:00
Nutritionist	jane smith	f	1000040.0	2024-08-06 08:30:00
Nutritionist	jane smith	f	1000082.0	2024-08-06 09:00:00
Nutritionist	jane smith	f	1000046.0	2024-08-06 09:30:00
Nutritionist	jane smith	f	1000084.0	2024-08-06 10:00:00
Nutritionist	jane smith	f	1000009.0	2024-08-06 10:30:00
Nutritionist	jane smith	f	1000047.0	2024-08-06 11:00:00
Nutritionist	jane smith	f	1000046.0	2024-08-06 11:30:00
Nutritionist	jane smith	f	1000063.0	2024-08-06 12:00:00
Nutritionist	jane smith	f	1000082.0	2024-08-06 12:30:00
Nutritionist	jane smith	f	1000034.0	2024-08-06 13:00:00
Nutritionist	jane smith	f	1000083.0	2024-08-06 13:30:00
Nutritionist	jane smith	f	1000080.0	2024-08-06 14:00:00
Nutritionist	jane smith	f	1000094.0	2024-08-06 14:30:00
Nutritionist	jane smith	f	1000036.0	2024-08-06 15:00:00
Nutritionist	jane smith	f	1000059.0	2024-08-06 15:30:00
Nutritionist	jane smith	f	1000034.0	2024-08-06 16:00:00
Nutritionist	jane smith	f	1000026.0	2024-08-06 16:30:00
Nutritionist	jane smith	t	\N	2024-08-07 08:00:00
Nutritionist	jane smith	t	\N	2024-08-07 08:30:00
Nutritionist	jane smith	t	\N	2024-08-07 09:00:00
Nutritionist	jane smith	t	\N	2024-08-07 09:30:00
Nutritionist	jane smith	t	\N	2024-08-07 10:00:00
Nutritionist	jane smith	t	\N	2024-08-07 10:30:00
Nutritionist	jane smith	f	1000004.0	2024-08-07 11:00:00
Nutritionist	jane smith	t	\N	2024-08-07 11:30:00
Care Coordinator	robert martinez	f	1000081.0	2024-08-30 15:30:00
Care Coordinator	robert martinez	t	\N	2024-08-30 16:00:00
Care Coordinator	robert martinez	t	\N	2024-08-30 16:30:00
Care Coordinator	robert martinez	t	\N	2024-08-31 09:00:00
Care Coordinator	robert martinez	f	1000032.0	2024-08-31 09:30:00
Care Coordinator	robert martinez	t	\N	2024-08-31 10:00:00
Care Coordinator	robert martinez	t	\N	2024-08-31 10:30:00
Care Coordinator	robert martinez	t	\N	2024-08-31 11:00:00
Care Coordinator	robert martinez	t	\N	2024-08-31 11:30:00
Care Coordinator	robert martinez	t	\N	2024-08-31 12:00:00
Care Coordinator	robert martinez	t	\N	2024-08-31 12:30:00
Care Coordinator	robert martinez	t	\N	2024-09-02 08:00:00
Care Coordinator	robert martinez	f	1000076.0	2024-09-02 08:30:00
Care Coordinator	robert martinez	t	\N	2024-09-02 09:00:00
Care Coordinator	robert martinez	t	\N	2024-09-02 09:30:00
Care Coordinator	robert martinez	f	1000091.0	2024-09-02 10:00:00
Care Coordinator	robert martinez	t	\N	2024-09-02 10:30:00
Care Coordinator	robert martinez	t	\N	2024-09-02 11:00:00
Care Coordinator	robert martinez	t	\N	2024-09-02 11:30:00
Care Coordinator	robert martinez	f	1000097.0	2024-09-02 12:00:00
Care Coordinator	robert martinez	f	1000071.0	2024-09-02 12:30:00
Care Coordinator	robert martinez	t	\N	2024-09-02 13:00:00
Care Coordinator	robert martinez	t	\N	2024-09-02 13:30:00
Care Coordinator	robert martinez	f	1000039.0	2024-09-02 14:00:00
Care Coordinator	robert martinez	f	1000023.0	2024-09-02 14:30:00
Care Coordinator	robert martinez	f	1000012.0	2024-09-02 15:00:00
Care Coordinator	robert martinez	t	\N	2024-09-02 15:30:00
Care Coordinator	robert martinez	t	\N	2024-09-02 16:00:00
Care Coordinator	robert martinez	t	\N	2024-09-02 16:30:00
Care Coordinator	robert martinez	f	1000010.0	2024-09-03 08:00:00
Care Coordinator	robert martinez	t	\N	2024-09-03 08:30:00
Care Coordinator	robert martinez	t	\N	2024-09-03 09:00:00
Care Coordinator	robert martinez	t	\N	2024-09-03 09:30:00
Care Coordinator	robert martinez	f	1000051.0	2024-09-03 10:00:00
Care Coordinator	robert martinez	t	\N	2024-09-03 10:30:00
Care Coordinator	robert martinez	t	\N	2024-09-03 11:00:00
Care Coordinator	robert martinez	t	\N	2024-09-03 11:30:00
Care Coordinator	robert martinez	t	\N	2024-09-03 12:00:00
Care Coordinator	robert martinez	t	\N	2024-09-03 12:30:00
Care Coordinator	robert martinez	f	1000036.0	2024-09-03 13:00:00
Care Coordinator	robert martinez	t	\N	2024-09-03 13:30:00
Care Coordinator	robert martinez	t	\N	2024-09-03 14:00:00
Care Coordinator	robert martinez	f	1000035.0	2024-09-03 14:30:00
Care Coordinator	robert martinez	t	\N	2024-09-03 15:00:00
Care Coordinator	robert martinez	f	1000090.0	2024-09-03 15:30:00
Care Coordinator	robert martinez	f	1000058.0	2024-09-03 16:00:00
Care Coordinator	robert martinez	t	\N	2024-09-03 16:30:00
Pharmacist	michael green	t	\N	2024-09-02 15:30:00
Pharmacist	michael green	f	1000054.0	2024-09-02 16:00:00
Pharmacist	michael green	t	\N	2024-09-02 16:30:00
Pharmacist	michael green	t	\N	2024-09-03 08:00:00
Pharmacist	michael green	f	1000082.0	2024-09-03 08:30:00
Pharmacist	michael green	t	\N	2024-09-03 09:00:00
Pharmacist	michael green	f	1000073.0	2024-09-03 09:30:00
Pharmacist	michael green	t	\N	2024-09-03 10:00:00
Pharmacist	michael green	f	1000099.0	2024-09-03 10:30:00
Pharmacist	michael green	t	\N	2024-09-03 11:00:00
Pharmacist	michael green	t	\N	2024-09-03 11:30:00
Pharmacist	michael green	f	1000043.0	2024-09-03 12:00:00
Pharmacist	michael green	f	1000043.0	2024-09-03 12:30:00
Pharmacist	michael green	t	\N	2024-09-03 13:00:00
Pharmacist	michael green	t	\N	2024-09-03 13:30:00
Pharmacist	michael green	t	\N	2024-09-03 14:00:00
Pharmacist	michael green	t	\N	2024-09-03 14:30:00
Occupational Therapist	lisa brown	f	1000096.0	2024-08-05 08:00:00
Occupational Therapist	lisa brown	f	1000078.0	2024-08-05 08:30:00
Occupational Therapist	lisa brown	f	1000000.0	2024-08-05 09:00:00
Occupational Therapist	lisa brown	f	1000045.0	2024-08-05 09:30:00
Occupational Therapist	lisa brown	f	1000055.0	2024-08-05 10:00:00
Occupational Therapist	lisa brown	f	1000057.0	2024-08-05 10:30:00
Occupational Therapist	lisa brown	f	1000069.0	2024-08-05 11:00:00
Occupational Therapist	lisa brown	f	1000071.0	2024-08-05 11:30:00
Occupational Therapist	lisa brown	f	1000019.0	2024-08-05 12:00:00
Occupational Therapist	lisa brown	f	1000045.0	2024-08-05 12:30:00
Occupational Therapist	lisa brown	f	1000047.0	2024-08-05 13:00:00
Occupational Therapist	lisa brown	f	1000032.0	2024-08-05 13:30:00
Occupational Therapist	lisa brown	f	1000025.0	2024-08-05 14:00:00
Occupational Therapist	lisa brown	f	1000097.0	2024-08-05 14:30:00
Occupational Therapist	lisa brown	f	1000084.0	2024-08-05 15:00:00
Occupational Therapist	lisa brown	f	1000047.0	2024-08-05 15:30:00
Occupational Therapist	lisa brown	f	1000046.0	2024-08-05 16:00:00
Occupational Therapist	lisa brown	f	1000068.0	2024-08-05 16:30:00
Occupational Therapist	lisa brown	f	1000035.0	2024-08-06 08:00:00
Occupational Therapist	lisa brown	f	1000004.0	2024-08-06 08:30:00
Occupational Therapist	lisa brown	f	1000095.0	2024-08-06 09:00:00
Occupational Therapist	lisa brown	f	1000019.0	2024-08-06 09:30:00
Occupational Therapist	lisa brown	f	1000042.0	2024-08-06 10:00:00
Occupational Therapist	lisa brown	f	1000048.0	2024-08-06 10:30:00
Occupational Therapist	lisa brown	f	1000064.0	2024-08-06 11:00:00
Occupational Therapist	lisa brown	f	1000035.0	2024-08-06 11:30:00
Occupational Therapist	lisa brown	f	1000081.0	2024-08-06 12:00:00
Occupational Therapist	lisa brown	f	1000035.0	2024-08-06 12:30:00
Occupational Therapist	lisa brown	f	1000020.0	2024-08-06 13:00:00
Occupational Therapist	lisa brown	f	1000017.0	2024-08-06 13:30:00
Pharmacist	michael green	f	1000094.0	2024-08-05 08:00:00
Pharmacist	michael green	f	1000080.0	2024-08-05 08:30:00
Pharmacist	michael green	f	1000027.0	2024-08-05 09:00:00
Pharmacist	michael green	f	1000033.0	2024-08-05 09:30:00
Pharmacist	michael green	f	1000097.0	2024-08-05 10:00:00
Pharmacist	michael green	f	1000040.0	2024-08-05 10:30:00
Pharmacist	michael green	f	1000072.0	2024-08-05 11:00:00
Pharmacist	michael green	f	1000004.0	2024-08-05 11:30:00
Pharmacist	michael green	f	1000008.0	2024-08-05 12:00:00
Pharmacist	michael green	f	1000072.0	2024-08-05 12:30:00
Pharmacist	michael green	f	1000055.0	2024-08-05 13:00:00
Pharmacist	michael green	f	1000033.0	2024-08-05 13:30:00
Pharmacist	michael green	f	1000025.0	2024-08-05 14:00:00
Pharmacist	michael green	f	1000075.0	2024-08-05 14:30:00
Pharmacist	michael green	f	1000014.0	2024-08-05 15:00:00
Pharmacist	michael green	f	1000039.0	2024-08-05 15:30:00
Pharmacist	michael green	f	1000036.0	2024-08-05 16:00:00
Pharmacist	michael green	f	1000094.0	2024-08-05 16:30:00
Pharmacist	michael green	f	1000030.0	2024-08-06 08:00:00
Pharmacist	michael green	f	1000052.0	2024-08-06 08:30:00
Pharmacist	michael green	f	1000004.0	2024-08-06 09:00:00
Pharmacist	michael green	f	1000049.0	2024-08-06 09:30:00
Pharmacist	michael green	f	1000024.0	2024-08-06 10:00:00
Pharmacist	michael green	f	1000009.0	2024-08-06 10:30:00
Pharmacist	michael green	f	1000041.0	2024-08-06 11:00:00
Pharmacist	michael green	f	1000033.0	2024-08-06 11:30:00
Pharmacist	michael green	f	1000067.0	2024-08-06 12:00:00
Pharmacist	michael green	f	1000081.0	2024-08-06 12:30:00
Pharmacist	michael green	f	1000050.0	2024-08-06 13:00:00
Pharmacist	michael green	f	1000080.0	2024-08-06 13:30:00
Pharmacist	michael green	f	1000058.0	2024-08-06 14:00:00
Pharmacist	michael green	f	1000067.0	2024-08-06 14:30:00
Pharmacist	michael green	f	1000082.0	2024-08-06 15:00:00
Pharmacist	michael green	f	1000098.0	2024-08-06 15:30:00
Pharmacist	michael green	f	1000090.0	2024-08-06 16:00:00
Pharmacist	michael green	f	1000064.0	2024-08-06 16:30:00
Pharmacist	michael green	t	\N	2024-08-07 08:00:00
Pharmacist	michael green	t	\N	2024-08-07 08:30:00
Pharmacist	michael green	f	1000064.0	2024-08-07 09:00:00
Pharmacist	michael green	t	\N	2024-08-07 09:30:00
Pharmacist	michael green	f	1000033.0	2024-08-07 10:00:00
Pharmacist	michael green	t	\N	2024-08-07 10:30:00
Pharmacist	michael green	t	\N	2024-08-07 11:00:00
Pharmacist	michael green	t	\N	2024-08-07 11:30:00
Pharmacist	michael green	t	\N	2024-08-07 12:00:00
Pharmacist	michael green	t	\N	2024-08-07 12:30:00
Pharmacist	michael green	t	\N	2024-08-07 13:00:00
Pharmacist	michael green	t	\N	2024-08-07 13:30:00
Pharmacist	michael green	t	\N	2024-08-07 14:00:00
Pharmacist	michael green	t	\N	2024-08-07 14:30:00
Pharmacist	michael green	f	1000089.0	2024-08-07 15:00:00
Pharmacist	michael green	t	\N	2024-08-07 15:30:00
Pharmacist	michael green	t	\N	2024-08-07 16:00:00
Pharmacist	michael green	f	1000038.0	2024-08-07 16:30:00
Pharmacist	michael green	t	\N	2024-08-08 08:00:00
Pharmacist	michael green	t	\N	2024-08-08 08:30:00
Pharmacist	michael green	t	\N	2024-08-08 09:00:00
Pharmacist	michael green	t	\N	2024-08-08 09:30:00
Pharmacist	michael green	f	1000048.0	2024-08-08 10:00:00
Pharmacist	michael green	t	\N	2024-08-08 10:30:00
Pharmacist	michael green	f	1000081.0	2024-08-08 11:00:00
Pharmacist	michael green	t	\N	2024-08-08 11:30:00
Pharmacist	michael green	t	\N	2024-08-08 12:00:00
Pharmacist	michael green	t	\N	2024-08-08 12:30:00
Pharmacist	michael green	f	1000001.0	2024-08-08 13:00:00
Pharmacist	michael green	t	\N	2024-08-08 13:30:00
Pharmacist	michael green	t	\N	2024-08-08 14:00:00
Pharmacist	michael green	t	\N	2024-08-08 14:30:00
Pharmacist	michael green	t	\N	2024-08-08 15:00:00
Pharmacist	michael green	t	\N	2024-08-08 15:30:00
Pharmacist	michael green	f	1000012.0	2024-08-08 16:00:00
Pharmacist	michael green	f	1000059.0	2024-08-08 16:30:00
Pharmacist	michael green	t	\N	2024-08-09 08:00:00
Pharmacist	michael green	t	\N	2024-08-09 08:30:00
Pharmacist	michael green	t	\N	2024-08-09 09:00:00
Pharmacist	michael green	t	\N	2024-08-09 09:30:00
Pharmacist	michael green	t	\N	2024-08-09 10:00:00
Pharmacist	michael green	f	1000058.0	2024-08-09 10:30:00
Pharmacist	michael green	t	\N	2024-08-09 11:00:00
Pharmacist	michael green	f	1000058.0	2024-08-09 11:30:00
Pharmacist	michael green	f	1000001.0	2024-08-09 12:00:00
Pharmacist	michael green	t	\N	2024-08-09 12:30:00
Pharmacist	michael green	f	1000080.0	2024-08-09 13:00:00
Pharmacist	michael green	f	1000076.0	2024-08-09 13:30:00
Pharmacist	michael green	t	\N	2024-08-09 14:00:00
Pharmacist	michael green	t	\N	2024-08-09 14:30:00
Pharmacist	michael green	t	\N	2024-08-09 15:00:00
Pharmacist	michael green	f	1000056.0	2024-08-09 15:30:00
Pharmacist	michael green	t	\N	2024-08-09 16:00:00
Pharmacist	michael green	t	\N	2024-08-09 16:30:00
Pharmacist	michael green	t	\N	2024-08-10 09:00:00
Pharmacist	michael green	t	\N	2024-08-10 09:30:00
Pharmacist	michael green	f	1000005.0	2024-08-10 10:00:00
Pharmacist	michael green	t	\N	2024-08-10 10:30:00
Pharmacist	michael green	t	\N	2024-08-10 11:00:00
Pharmacist	michael green	f	1000100.0	2024-08-10 11:30:00
Pharmacist	michael green	f	1000095.0	2024-08-10 12:00:00
Pharmacist	michael green	f	1000054.0	2024-08-10 12:30:00
Pharmacist	michael green	t	\N	2024-08-12 08:00:00
Pharmacist	michael green	t	\N	2024-08-12 08:30:00
Pharmacist	michael green	t	\N	2024-08-12 09:00:00
Pharmacist	michael green	f	1000024.0	2024-08-12 09:30:00
Pharmacist	michael green	t	\N	2024-08-12 10:00:00
Pharmacist	michael green	t	\N	2024-08-12 10:30:00
Pharmacist	michael green	t	\N	2024-08-12 11:00:00
Pharmacist	michael green	f	1000049.0	2024-08-12 11:30:00
Pharmacist	michael green	f	1000041.0	2024-08-12 12:00:00
Pharmacist	michael green	f	1000042.0	2024-08-12 12:30:00
Pharmacist	michael green	t	\N	2024-08-12 13:00:00
Pharmacist	michael green	f	1000058.0	2024-08-12 13:30:00
Pharmacist	michael green	t	\N	2024-08-12 14:00:00
Pharmacist	michael green	t	\N	2024-08-12 14:30:00
Pharmacist	michael green	t	\N	2024-08-12 15:00:00
Pharmacist	michael green	f	1000002.0	2024-08-12 15:30:00
Pharmacist	michael green	f	1000006.0	2024-08-12 16:00:00
Pharmacist	michael green	f	1000000.0	2024-08-12 16:30:00
Pharmacist	michael green	t	\N	2024-08-13 08:00:00
Pharmacist	michael green	f	1000001.0	2024-08-13 08:30:00
Pharmacist	michael green	f	1000045.0	2024-08-13 09:00:00
Pharmacist	michael green	f	1000081.0	2024-08-13 09:30:00
Pharmacist	michael green	f	1000033.0	2024-08-13 10:00:00
Pharmacist	michael green	t	\N	2024-08-13 10:30:00
Pharmacist	michael green	t	\N	2024-08-13 11:00:00
Pharmacist	michael green	f	1000006.0	2024-08-13 11:30:00
Pharmacist	michael green	f	1000022.0	2024-08-13 12:00:00
Pharmacist	michael green	t	\N	2024-08-13 12:30:00
Pharmacist	michael green	f	1000090.0	2024-08-13 13:00:00
Pharmacist	michael green	t	\N	2024-08-13 13:30:00
Pharmacist	michael green	t	\N	2024-08-13 14:00:00
Pharmacist	michael green	f	1000055.0	2024-08-13 14:30:00
Pharmacist	michael green	f	1000011.0	2024-08-13 15:00:00
Pharmacist	michael green	t	\N	2024-08-13 15:30:00
Pharmacist	michael green	t	\N	2024-08-13 16:00:00
Pharmacist	michael green	t	\N	2024-08-13 16:30:00
Pharmacist	michael green	f	1000033.0	2024-08-14 08:00:00
Pharmacist	michael green	t	\N	2024-08-14 08:30:00
Pharmacist	michael green	f	1000017.0	2024-08-14 09:00:00
Pharmacist	michael green	t	\N	2024-08-14 09:30:00
Pharmacist	michael green	f	1000016.0	2024-08-14 10:00:00
Pharmacist	michael green	t	\N	2024-08-14 10:30:00
Pharmacist	michael green	t	\N	2024-08-14 11:00:00
Pharmacist	michael green	t	\N	2024-08-14 11:30:00
Pharmacist	michael green	t	\N	2024-08-14 12:00:00
Pharmacist	michael green	t	\N	2024-08-14 12:30:00
Pharmacist	michael green	t	\N	2024-08-14 13:00:00
Pharmacist	michael green	t	\N	2024-08-14 13:30:00
Pharmacist	michael green	t	\N	2024-08-14 14:00:00
Pharmacist	michael green	t	\N	2024-08-14 14:30:00
Pharmacist	michael green	t	\N	2024-08-14 15:00:00
Pharmacist	michael green	t	\N	2024-08-14 15:30:00
Pharmacist	michael green	t	\N	2024-08-14 16:00:00
Pharmacist	michael green	t	\N	2024-08-14 16:30:00
Pharmacist	michael green	f	1000020.0	2024-08-15 08:00:00
Pharmacist	michael green	f	1000097.0	2024-08-15 08:30:00
Pharmacist	michael green	f	1000031.0	2024-08-15 09:00:00
Pharmacist	michael green	f	1000032.0	2024-08-15 09:30:00
Pharmacist	michael green	t	\N	2024-08-15 10:00:00
Pharmacist	michael green	t	\N	2024-08-15 10:30:00
Pharmacist	michael green	t	\N	2024-08-15 11:00:00
Pharmacist	michael green	t	\N	2024-08-15 11:30:00
Pharmacist	michael green	f	1000008.0	2024-08-15 12:00:00
Pharmacist	michael green	t	\N	2024-08-15 12:30:00
Pharmacist	michael green	t	\N	2024-08-15 13:00:00
Pharmacist	michael green	t	\N	2024-08-15 13:30:00
Pharmacist	michael green	t	\N	2024-08-15 14:00:00
Pharmacist	michael green	t	\N	2024-08-15 14:30:00
Pharmacist	michael green	t	\N	2024-08-15 15:00:00
Pharmacist	michael green	t	\N	2024-08-15 15:30:00
Pharmacist	michael green	t	\N	2024-08-15 16:00:00
Pharmacist	michael green	f	1000040.0	2024-08-15 16:30:00
Pharmacist	michael green	t	\N	2024-08-16 08:00:00
Pharmacist	michael green	t	\N	2024-08-16 08:30:00
Pharmacist	michael green	f	1000011.0	2024-08-16 09:00:00
Pharmacist	michael green	t	\N	2024-08-16 09:30:00
Pharmacist	michael green	t	\N	2024-08-16 10:00:00
Pharmacist	michael green	t	\N	2024-08-16 10:30:00
Pharmacist	michael green	f	1000051.0	2024-08-16 11:00:00
Pharmacist	michael green	t	\N	2024-08-16 11:30:00
Pharmacist	michael green	t	\N	2024-08-16 12:00:00
Pharmacist	michael green	f	1000045.0	2024-08-16 12:30:00
Pharmacist	michael green	t	\N	2024-08-16 13:00:00
Pharmacist	michael green	f	1000007.0	2024-08-16 13:30:00
Pharmacist	michael green	t	\N	2024-08-16 14:00:00
Pharmacist	michael green	f	1000007.0	2024-08-16 14:30:00
Pharmacist	michael green	t	\N	2024-08-16 15:00:00
Pharmacist	michael green	t	\N	2024-08-16 15:30:00
Pharmacist	michael green	t	\N	2024-08-16 16:00:00
Pharmacist	michael green	f	1000061.0	2024-08-16 16:30:00
Pharmacist	michael green	t	\N	2024-08-17 09:00:00
Pharmacist	michael green	t	\N	2024-08-17 09:30:00
Pharmacist	michael green	t	\N	2024-08-17 10:00:00
Pharmacist	michael green	f	1000023.0	2024-08-17 10:30:00
Pharmacist	michael green	t	\N	2024-08-17 11:00:00
Pharmacist	michael green	f	1000090.0	2024-08-17 11:30:00
Pharmacist	michael green	t	\N	2024-08-17 12:00:00
Pharmacist	michael green	t	\N	2024-08-17 12:30:00
Pharmacist	michael green	f	1000099.0	2024-08-19 08:00:00
Pharmacist	michael green	t	\N	2024-08-19 08:30:00
Pharmacist	michael green	t	\N	2024-08-19 09:00:00
Pharmacist	michael green	f	1000056.0	2024-08-19 09:30:00
Pharmacist	michael green	f	1000065.0	2024-08-19 10:00:00
Pharmacist	michael green	f	1000022.0	2024-08-19 10:30:00
Pharmacist	michael green	f	1000087.0	2024-08-19 11:00:00
Pharmacist	michael green	t	\N	2024-08-19 11:30:00
Pharmacist	michael green	t	\N	2024-08-21 11:30:00
Pharmacist	michael green	t	\N	2024-08-21 12:00:00
Pharmacist	michael green	t	\N	2024-08-21 12:30:00
Pharmacist	michael green	f	1000055.0	2024-08-21 13:00:00
Pharmacist	michael green	t	\N	2024-08-21 13:30:00
Pharmacist	michael green	f	1000073.0	2024-08-21 14:00:00
Pharmacist	michael green	t	\N	2024-08-21 14:30:00
Pharmacist	michael green	f	1000075.0	2024-08-21 15:00:00
Pharmacist	michael green	t	\N	2024-08-21 15:30:00
Pharmacist	michael green	t	\N	2024-08-21 16:00:00
Pharmacist	michael green	t	\N	2024-08-21 16:30:00
Pharmacist	michael green	t	\N	2024-08-22 08:00:00
Pharmacist	michael green	t	\N	2024-08-22 08:30:00
Pharmacist	michael green	t	\N	2024-08-22 09:00:00
Pharmacist	michael green	f	1000023.0	2024-08-22 09:30:00
Pharmacist	michael green	t	\N	2024-08-22 10:00:00
Pharmacist	michael green	t	\N	2024-08-22 10:30:00
Pharmacist	michael green	f	1000098.0	2024-08-22 11:00:00
Pharmacist	michael green	t	\N	2024-08-22 11:30:00
Pharmacist	michael green	f	1000060.0	2024-08-22 12:00:00
Pharmacist	michael green	t	\N	2024-08-22 12:30:00
Pharmacist	michael green	f	1000016.0	2024-08-22 13:00:00
Pharmacist	michael green	f	1000067.0	2024-08-22 13:30:00
Pharmacist	michael green	t	\N	2024-08-22 14:00:00
Pharmacist	michael green	f	1000038.0	2024-08-22 14:30:00
Pharmacist	michael green	t	\N	2024-08-22 15:00:00
Pharmacist	michael green	f	1000095.0	2024-08-22 15:30:00
Pharmacist	michael green	f	1000058.0	2024-08-22 16:00:00
Occupational Therapist	lisa brown	f	1000079.0	2024-08-07 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-07 16:30:00
Occupational Therapist	lisa brown	f	12345678.0	2024-08-08 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 08:30:00
Occupational Therapist	lisa brown	f	1000032.0	2024-08-08 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 09:30:00
Occupational Therapist	lisa brown	f	10123224.0	2024-08-08 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 10:30:00
Occupational Therapist	lisa brown	f	1000058.0	2024-08-08 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 11:30:00
Occupational Therapist	lisa brown	f	1000043.0	2024-08-08 12:00:00
Occupational Therapist	lisa brown	f	1000013.0	2024-08-08 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 14:00:00
Occupational Therapist	lisa brown	f	1000059.0	2024-08-08 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 15:00:00
Occupational Therapist	lisa brown	f	1000038.0	2024-08-08 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-08 16:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 12:00:00
Occupational Therapist	lisa brown	f	1000042.0	2024-08-09 12:30:00
Occupational Therapist	lisa brown	f	1000089.0	2024-08-09 13:00:00
Occupational Therapist	lisa brown	f	1000001.0	2024-08-09 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-09 16:30:00
Occupational Therapist	lisa brown	f	1000077.0	2024-08-10 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-10 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-10 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-10 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-10 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-10 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-10 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-10 12:30:00
Occupational Therapist	lisa brown	f	1000035.0	2024-08-12 08:00:00
Occupational Therapist	lisa brown	f	1000082.0	2024-08-12 08:30:00
Occupational Therapist	lisa brown	f	1000019.0	2024-08-12 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 10:30:00
Occupational Therapist	lisa brown	f	1000016.0	2024-08-12 11:00:00
Occupational Therapist	lisa brown	f	1000066.0	2024-08-12 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 12:30:00
Occupational Therapist	lisa brown	f	1000099.0	2024-08-12 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 13:30:00
Occupational Therapist	lisa brown	f	1000086.0	2024-08-12 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 14:30:00
Occupational Therapist	lisa brown	f	1000001.0	2024-08-12 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-12 16:30:00
Occupational Therapist	lisa brown	f	1000008.0	2024-08-13 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 08:30:00
Occupational Therapist	lisa brown	f	1000021.0	2024-08-13 09:00:00
Occupational Therapist	lisa brown	f	1000052.0	2024-08-13 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 14:30:00
Occupational Therapist	lisa brown	f	1000085.0	2024-08-13 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-13 16:00:00
Occupational Therapist	lisa brown	f	1000045.0	2024-08-13 16:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 08:30:00
Occupational Therapist	lisa brown	f	1000081.0	2024-08-14 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 10:00:00
Occupational Therapist	lisa brown	f	1000048.0	2024-08-14 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 11:00:00
Occupational Therapist	lisa brown	f	1000051.0	2024-08-14 11:30:00
Occupational Therapist	lisa brown	f	1000022.0	2024-08-14 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 12:30:00
Occupational Therapist	lisa brown	f	1000057.0	2024-08-14 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-14 16:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-15 16:30:00
Occupational Therapist	lisa brown	f	1000003.0	2024-08-16 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 09:00:00
Occupational Therapist	lisa brown	f	1000003.0	2024-08-16 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 15:00:00
Occupational Therapist	lisa brown	f	1000022.0	2024-08-16 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-16 16:30:00
Occupational Therapist	lisa brown	f	1000021.0	2024-08-17 09:00:00
Occupational Therapist	lisa brown	f	1000005.0	2024-08-17 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-17 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-17 10:30:00
Occupational Therapist	lisa brown	f	1000092.0	2024-08-17 11:00:00
Occupational Therapist	lisa brown	f	1000059.0	2024-08-17 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-17 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-17 12:30:00
Occupational Therapist	lisa brown	f	1000009.0	2024-08-19 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 09:00:00
Occupational Therapist	lisa brown	f	1000094.0	2024-08-19 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 10:30:00
Occupational Therapist	lisa brown	f	1000060.0	2024-08-19 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 11:30:00
Occupational Therapist	lisa brown	f	1000038.0	2024-08-19 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 15:00:00
Occupational Therapist	lisa brown	f	1000010.0	2024-08-19 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-19 16:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 08:30:00
Occupational Therapist	lisa brown	f	1000073.0	2024-08-20 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 11:00:00
Occupational Therapist	lisa brown	f	1000084.0	2024-08-20 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 12:30:00
Occupational Therapist	lisa brown	f	1000041.0	2024-08-20 13:00:00
Occupational Therapist	lisa brown	f	1000021.0	2024-08-20 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 15:00:00
Occupational Therapist	lisa brown	f	1000071.0	2024-08-20 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-20 16:30:00
Occupational Therapist	lisa brown	f	1000065.0	2024-08-21 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 10:00:00
Occupational Therapist	lisa brown	f	1000096.0	2024-08-21 10:30:00
Occupational Therapist	lisa brown	f	1000079.0	2024-08-21 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 12:30:00
Occupational Therapist	lisa brown	f	1000067.0	2024-08-21 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 13:30:00
Occupational Therapist	lisa brown	f	1000034.0	2024-08-21 14:00:00
Occupational Therapist	lisa brown	f	1000093.0	2024-08-21 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-21 16:00:00
Occupational Therapist	lisa brown	f	1000076.0	2024-08-21 16:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 08:00:00
Occupational Therapist	lisa brown	f	1000043.0	2024-08-22 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 11:00:00
Occupational Therapist	lisa brown	f	1000055.0	2024-08-22 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 12:00:00
Occupational Therapist	lisa brown	f	1000062.0	2024-08-22 12:30:00
Occupational Therapist	lisa brown	f	1000061.0	2024-08-22 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 15:00:00
Occupational Therapist	lisa brown	f	1000058.0	2024-08-22 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-22 16:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 09:00:00
Occupational Therapist	lisa brown	f	1000013.0	2024-08-23 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 14:00:00
Occupational Therapist	lisa brown	f	1000040.0	2024-08-23 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-23 16:30:00
Occupational Therapist	lisa brown	f	1000032.0	2024-08-24 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-24 09:30:00
Occupational Therapist	lisa brown	f	1000009.0	2024-08-24 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-24 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-24 11:00:00
Occupational Therapist	lisa brown	f	1000015.0	2024-08-24 11:30:00
Occupational Therapist	lisa brown	f	1000061.0	2024-08-24 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-24 12:30:00
Occupational Therapist	lisa brown	f	1000030.0	2024-08-26 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 11:30:00
Occupational Therapist	lisa brown	f	1000063.0	2024-08-26 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 12:30:00
Occupational Therapist	lisa brown	f	1000045.0	2024-08-26 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 14:00:00
Occupational Therapist	lisa brown	f	1000049.0	2024-08-26 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-26 16:00:00
Occupational Therapist	lisa brown	f	1000052.0	2024-08-26 16:30:00
Occupational Therapist	lisa brown	f	1000064.0	2024-08-27 08:00:00
Occupational Therapist	lisa brown	f	1000012.0	2024-08-27 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 10:00:00
Occupational Therapist	lisa brown	f	1000059.0	2024-08-27 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 13:30:00
Occupational Therapist	lisa brown	f	1000025.0	2024-08-27 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 14:30:00
Occupational Therapist	lisa brown	f	1000050.0	2024-08-27 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-27 16:00:00
Occupational Therapist	lisa brown	f	1000076.0	2024-08-27 16:30:00
Occupational Therapist	lisa brown	f	1000020.0	2024-08-28 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 09:00:00
Occupational Therapist	lisa brown	f	1000070.0	2024-08-28 09:30:00
Occupational Therapist	lisa brown	f	1000066.0	2024-08-28 10:00:00
Occupational Therapist	lisa brown	f	1000009.0	2024-08-28 10:30:00
Occupational Therapist	lisa brown	f	1000004.0	2024-08-28 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 14:00:00
Occupational Therapist	lisa brown	f	1000042.0	2024-08-28 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 15:00:00
Occupational Therapist	lisa brown	f	1000094.0	2024-08-28 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-28 16:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 09:30:00
Occupational Therapist	lisa brown	f	1000000.0	2024-08-29 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 11:00:00
Occupational Therapist	lisa brown	f	1000000.0	2024-08-29 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 12:30:00
Occupational Therapist	lisa brown	f	1000090.0	2024-08-29 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 14:30:00
Occupational Therapist	lisa brown	f	1000015.0	2024-08-29 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-29 16:30:00
Occupational Therapist	lisa brown	f	1000079.0	2024-08-30 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 09:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 10:30:00
Occupational Therapist	lisa brown	f	1000061.0	2024-08-30 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 12:30:00
Occupational Therapist	lisa brown	f	1000038.0	2024-08-30 13:00:00
Occupational Therapist	lisa brown	f	1000005.0	2024-08-30 13:30:00
Occupational Therapist	lisa brown	f	1000034.0	2024-08-30 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 14:30:00
Occupational Therapist	lisa brown	f	1000083.0	2024-08-30 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-08-30 16:00:00
Occupational Therapist	lisa brown	f	1000055.0	2024-08-30 16:30:00
Occupational Therapist	lisa brown	f	1000030.0	2024-08-31 09:00:00
Occupational Therapist	lisa brown	f	1000094.0	2024-08-31 09:30:00
Occupational Therapist	lisa brown	f	1000030.0	2024-08-31 10:00:00
Occupational Therapist	lisa brown	f	1000043.0	2024-08-31 10:30:00
Occupational Therapist	lisa brown	f	1000017.0	2024-08-31 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-08-31 11:30:00
Occupational Therapist	lisa brown	f	1000045.0	2024-08-31 12:00:00
Occupational Therapist	lisa brown	f	1000093.0	2024-08-31 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 08:00:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 09:00:00
Occupational Therapist	lisa brown	f	1000024.0	2024-09-02 09:30:00
Occupational Therapist	lisa brown	f	1000098.0	2024-09-02 10:00:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 10:30:00
Occupational Therapist	lisa brown	f	1000046.0	2024-09-02 11:00:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 12:30:00
Occupational Therapist	lisa brown	f	1000003.0	2024-09-02 13:00:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 14:00:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 14:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 15:00:00
Occupational Therapist	lisa brown	f	1000077.0	2024-09-02 15:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-02 16:00:00
Occupational Therapist	lisa brown	f	1000047.0	2024-09-02 16:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 08:00:00
Occupational Therapist	lisa brown	f	1000044.0	2024-09-03 08:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 09:00:00
Occupational Therapist	lisa brown	f	1000058.0	2024-09-03 09:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 10:00:00
Occupational Therapist	lisa brown	f	1000055.0	2024-09-03 10:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 11:00:00
Occupational Therapist	lisa brown	f	1000031.0	2024-09-03 11:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 12:00:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 12:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 13:00:00
Occupational Therapist	lisa brown	f	1000078.0	2024-09-03 13:30:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 14:00:00
Occupational Therapist	lisa brown	f	1000023.0	2024-09-03 14:30:00
Occupational Therapist	lisa brown	f	1000074.0	2024-09-03 15:00:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 15:30:00
Occupational Therapist	lisa brown	f	1000085.0	2024-09-03 16:00:00
Occupational Therapist	lisa brown	t	\N	2024-09-03 16:30:00
Pharmacist	michael green	t	\N	2024-09-03 15:00:00
Pharmacist	michael green	t	\N	2024-09-03 15:30:00
Pharmacist	michael green	f	1000093.0	2024-09-03 16:00:00
Pharmacist	michael green	t	\N	2024-09-03 16:30:00
Physical Therapist	john doe	t	\N	2024-08-05 08:00:00
Physical Therapist	john doe	f	1000082.0	2024-08-05 08:30:00
Physical Therapist	john doe	f	1000048.0	2024-08-05 09:00:00
Physical Therapist	john doe	f	1000036.0	2024-08-05 09:30:00
Physical Therapist	john doe	f	1000024.0	2024-08-05 10:00:00
Physical Therapist	john doe	f	1000011.0	2024-08-05 10:30:00
Physical Therapist	john doe	f	1000061.0	2024-08-05 11:00:00
Physical Therapist	john doe	f	1000062.0	2024-08-05 11:30:00
Physical Therapist	john doe	f	1000046.0	2024-08-05 12:00:00
Physical Therapist	john doe	f	1000057.0	2024-08-05 12:30:00
Physical Therapist	john doe	f	1000088.0	2024-08-05 13:00:00
Physical Therapist	john doe	f	1000090.0	2024-08-05 13:30:00
Physical Therapist	john doe	f	1000069.0	2024-08-05 14:00:00
Physical Therapist	john doe	f	1000065.0	2024-08-05 14:30:00
Physical Therapist	john doe	f	1000026.0	2024-08-05 15:00:00
Physical Therapist	john doe	f	1000006.0	2024-08-05 15:30:00
Physical Therapist	john doe	f	1000029.0	2024-08-05 16:00:00
Physical Therapist	john doe	f	1000073.0	2024-08-05 16:30:00
Physical Therapist	john doe	f	1000018.0	2024-08-06 08:00:00
Physical Therapist	john doe	f	1000048.0	2024-08-06 08:30:00
Physical Therapist	john doe	f	1000085.0	2024-08-06 09:00:00
Physical Therapist	john doe	f	1000074.0	2024-08-06 09:30:00
Physical Therapist	john doe	f	1000094.0	2024-08-06 10:00:00
Physical Therapist	john doe	f	1000047.0	2024-08-06 10:30:00
Physical Therapist	john doe	f	1000087.0	2024-08-06 11:00:00
Physical Therapist	john doe	f	1000071.0	2024-08-06 11:30:00
Physical Therapist	john doe	f	1000059.0	2024-08-06 12:00:00
Physical Therapist	john doe	f	1000073.0	2024-08-06 12:30:00
Physical Therapist	john doe	f	1000042.0	2024-08-06 13:00:00
Physical Therapist	john doe	f	1000060.0	2024-08-06 13:30:00
Physical Therapist	john doe	f	1000033.0	2024-08-06 14:00:00
Physical Therapist	john doe	f	1000067.0	2024-08-06 14:30:00
Physical Therapist	john doe	f	1000039.0	2024-08-06 15:00:00
Physical Therapist	john doe	f	1000071.0	2024-08-06 15:30:00
Physical Therapist	john doe	f	1000047.0	2024-08-06 16:00:00
Physical Therapist	john doe	f	1000043.0	2024-08-06 16:30:00
Physical Therapist	john doe	t	\N	2024-08-07 08:00:00
Physical Therapist	john doe	t	\N	2024-08-07 08:30:00
Physical Therapist	john doe	f	1000097.0	2024-08-07 09:00:00
Geriatrician	daniel miller	f	1000059.0	2024-08-05 08:00:00
Physical Therapist	john doe	t	\N	2024-08-07 09:30:00
Physical Therapist	john doe	f	1000023.0	2024-08-07 10:00:00
Physical Therapist	john doe	t	\N	2024-08-07 10:30:00
Physical Therapist	john doe	t	\N	2024-08-07 11:00:00
Physical Therapist	john doe	t	\N	2024-08-07 11:30:00
Physical Therapist	john doe	f	1000073.0	2024-08-07 12:00:00
Physical Therapist	john doe	f	1000004.0	2024-08-07 12:30:00
Physical Therapist	john doe	t	\N	2024-08-07 13:00:00
Physical Therapist	john doe	f	1000002.0	2024-08-07 13:30:00
Physical Therapist	john doe	t	\N	2024-08-07 14:00:00
Physical Therapist	john doe	t	\N	2024-08-07 14:30:00
Physical Therapist	john doe	t	\N	2024-08-07 15:00:00
Physical Therapist	john doe	f	1000044.0	2024-08-07 15:30:00
Physical Therapist	john doe	t	\N	2024-08-07 16:00:00
Physical Therapist	john doe	t	\N	2024-08-07 16:30:00
Physical Therapist	john doe	t	\N	2024-08-08 08:00:00
Physical Therapist	john doe	f	1000086.0	2024-08-08 08:30:00
Physical Therapist	john doe	t	\N	2024-08-08 09:00:00
Physical Therapist	john doe	t	\N	2024-08-08 09:30:00
Physical Therapist	john doe	t	\N	2024-08-08 10:00:00
Physical Therapist	john doe	f	1000030.0	2024-08-08 10:30:00
Physical Therapist	john doe	f	1000065.0	2024-08-08 11:00:00
Physical Therapist	john doe	f	1000083.0	2024-08-08 11:30:00
Physical Therapist	john doe	t	\N	2024-08-08 12:00:00
Physical Therapist	john doe	f	1000005.0	2024-08-08 12:30:00
Physical Therapist	john doe	f	1000054.0	2024-08-08 13:00:00
Physical Therapist	john doe	t	\N	2024-08-08 13:30:00
Physical Therapist	john doe	t	\N	2024-08-08 14:00:00
Physical Therapist	john doe	f	1000057.0	2024-08-08 14:30:00
Physical Therapist	john doe	t	\N	2024-08-08 15:00:00
Physical Therapist	john doe	t	\N	2024-08-08 15:30:00
Physical Therapist	john doe	t	\N	2024-08-08 16:00:00
Physical Therapist	john doe	t	\N	2024-08-08 16:30:00
Physical Therapist	john doe	f	1000062.0	2024-08-09 08:00:00
Physical Therapist	john doe	f	1000068.0	2024-08-09 08:30:00
Physical Therapist	john doe	t	\N	2024-08-09 09:00:00
Physical Therapist	john doe	f	1000016.0	2024-08-09 09:30:00
Physical Therapist	john doe	f	1000069.0	2024-08-09 10:00:00
Physical Therapist	john doe	t	\N	2024-08-09 10:30:00
Physical Therapist	john doe	t	\N	2024-08-09 11:00:00
Physical Therapist	john doe	t	\N	2024-08-09 11:30:00
Physical Therapist	john doe	t	\N	2024-08-09 12:00:00
Physical Therapist	john doe	f	1000046.0	2024-08-09 12:30:00
Physical Therapist	john doe	t	\N	2024-08-09 13:00:00
Physical Therapist	john doe	t	\N	2024-08-09 13:30:00
Physical Therapist	john doe	t	\N	2024-08-09 14:00:00
Physical Therapist	john doe	t	\N	2024-08-09 14:30:00
Physical Therapist	john doe	t	\N	2024-08-09 15:00:00
Physical Therapist	john doe	t	\N	2024-08-09 15:30:00
Physical Therapist	john doe	t	\N	2024-08-09 16:00:00
Physical Therapist	john doe	t	\N	2024-08-09 16:30:00
Physical Therapist	john doe	t	\N	2024-08-10 09:00:00
Physical Therapist	john doe	f	1000032.0	2024-08-10 09:30:00
Physical Therapist	john doe	f	1000046.0	2024-08-10 10:00:00
Physical Therapist	john doe	t	\N	2024-08-10 10:30:00
Physical Therapist	john doe	t	\N	2024-08-10 11:00:00
Physical Therapist	john doe	t	\N	2024-08-10 11:30:00
Physical Therapist	john doe	t	\N	2024-08-10 12:00:00
Physical Therapist	john doe	t	\N	2024-08-10 12:30:00
Physical Therapist	john doe	t	\N	2024-08-12 08:00:00
Physical Therapist	john doe	t	\N	2024-08-12 08:30:00
Physical Therapist	john doe	f	1000093.0	2024-08-12 09:00:00
Physical Therapist	john doe	f	1000018.0	2024-08-12 09:30:00
Physical Therapist	john doe	t	\N	2024-08-12 10:00:00
Physical Therapist	john doe	f	1000081.0	2024-08-12 10:30:00
Physical Therapist	john doe	t	\N	2024-08-12 11:00:00
Physical Therapist	john doe	f	1000087.0	2024-08-12 11:30:00
Physical Therapist	john doe	t	\N	2024-08-12 12:00:00
Physical Therapist	john doe	t	\N	2024-08-12 12:30:00
Physical Therapist	john doe	t	\N	2024-08-12 13:00:00
Physical Therapist	john doe	t	\N	2024-08-12 13:30:00
Physical Therapist	john doe	f	1000079.0	2024-08-12 14:00:00
Physical Therapist	john doe	t	\N	2024-08-12 14:30:00
Physical Therapist	john doe	f	1000083.0	2024-08-12 15:00:00
Physical Therapist	john doe	f	1000065.0	2024-08-12 15:30:00
Physical Therapist	john doe	t	\N	2024-08-12 16:00:00
Physical Therapist	john doe	t	\N	2024-08-12 16:30:00
Physical Therapist	john doe	f	1000019.0	2024-08-13 08:00:00
Physical Therapist	john doe	t	\N	2024-08-13 08:30:00
Physical Therapist	john doe	f	1000100.0	2024-08-13 09:00:00
Physical Therapist	john doe	t	\N	2024-08-13 09:30:00
Physical Therapist	john doe	f	1000035.0	2024-08-13 10:00:00
Physical Therapist	john doe	t	\N	2024-08-13 10:30:00
Physical Therapist	john doe	t	\N	2024-08-13 11:00:00
Physical Therapist	john doe	f	1000068.0	2024-08-13 11:30:00
Physical Therapist	john doe	f	1000067.0	2024-08-13 12:00:00
Physical Therapist	john doe	f	1000007.0	2024-08-13 12:30:00
Physical Therapist	john doe	t	\N	2024-08-13 13:00:00
Physical Therapist	john doe	t	\N	2024-08-13 13:30:00
Physical Therapist	john doe	t	\N	2024-08-13 14:00:00
Physical Therapist	john doe	t	\N	2024-08-13 14:30:00
Physical Therapist	john doe	t	\N	2024-08-13 15:00:00
Physical Therapist	john doe	t	\N	2024-08-13 15:30:00
Physical Therapist	john doe	t	\N	2024-08-13 16:00:00
Physical Therapist	john doe	t	\N	2024-08-13 16:30:00
Physical Therapist	john doe	t	\N	2024-08-14 08:00:00
Physical Therapist	john doe	t	\N	2024-08-14 08:30:00
Physical Therapist	john doe	t	\N	2024-08-14 09:00:00
Physical Therapist	john doe	t	\N	2024-08-14 09:30:00
Physical Therapist	john doe	t	\N	2024-08-14 10:00:00
Physical Therapist	john doe	t	\N	2024-08-14 10:30:00
Physical Therapist	john doe	t	\N	2024-08-14 11:00:00
Physical Therapist	john doe	f	1000003.0	2024-08-14 11:30:00
Physical Therapist	john doe	f	1000002.0	2024-08-14 12:00:00
Physical Therapist	john doe	f	1000002.0	2024-08-14 12:30:00
Physical Therapist	john doe	f	1000079.0	2024-08-14 13:00:00
Physical Therapist	john doe	t	\N	2024-08-14 13:30:00
Physical Therapist	john doe	t	\N	2024-08-14 14:00:00
Physical Therapist	john doe	f	1000007.0	2024-08-14 14:30:00
Physical Therapist	john doe	f	1000046.0	2024-08-14 15:00:00
Physical Therapist	john doe	t	\N	2024-08-14 15:30:00
Physical Therapist	john doe	t	\N	2024-08-14 16:00:00
Physical Therapist	john doe	t	\N	2024-08-14 16:30:00
Physical Therapist	john doe	t	\N	2024-08-15 08:00:00
Physical Therapist	john doe	t	\N	2024-08-15 08:30:00
Physical Therapist	john doe	t	\N	2024-08-15 09:00:00
Physical Therapist	john doe	t	\N	2024-08-15 09:30:00
Physical Therapist	john doe	t	\N	2024-08-15 10:00:00
Physical Therapist	john doe	t	\N	2024-08-15 10:30:00
Physical Therapist	john doe	f	1000099.0	2024-08-15 11:00:00
Physical Therapist	john doe	t	\N	2024-08-15 11:30:00
Physical Therapist	john doe	t	\N	2024-08-15 12:00:00
Physical Therapist	john doe	t	\N	2024-08-15 12:30:00
Physical Therapist	john doe	f	1000029.0	2024-08-15 13:00:00
Physical Therapist	john doe	t	\N	2024-08-15 13:30:00
Physical Therapist	john doe	t	\N	2024-08-15 14:00:00
Physical Therapist	john doe	f	1000023.0	2024-08-15 14:30:00
Physical Therapist	john doe	t	\N	2024-08-15 15:00:00
Physical Therapist	john doe	f	1000099.0	2024-08-15 15:30:00
Physical Therapist	john doe	t	\N	2024-08-15 16:00:00
Physical Therapist	john doe	f	1000085.0	2024-08-15 16:30:00
Physical Therapist	john doe	f	1000004.0	2024-08-16 08:00:00
Physical Therapist	john doe	t	\N	2024-08-16 08:30:00
Physical Therapist	john doe	t	\N	2024-08-16 09:00:00
Physical Therapist	john doe	t	\N	2024-08-16 09:30:00
Physical Therapist	john doe	t	\N	2024-08-16 10:00:00
Physical Therapist	john doe	f	1000077.0	2024-08-16 10:30:00
Physical Therapist	john doe	t	\N	2024-08-16 11:00:00
Physical Therapist	john doe	t	\N	2024-08-16 11:30:00
Physical Therapist	john doe	t	\N	2024-08-16 12:00:00
Physical Therapist	john doe	t	\N	2024-08-16 12:30:00
Physical Therapist	john doe	f	1000009.0	2024-08-16 13:00:00
Physical Therapist	john doe	t	\N	2024-08-16 13:30:00
Physical Therapist	john doe	f	1000009.0	2024-08-16 14:00:00
Physical Therapist	john doe	f	1000027.0	2024-08-16 14:30:00
Physical Therapist	john doe	t	\N	2024-08-16 15:00:00
Physical Therapist	john doe	f	1000018.0	2024-08-16 15:30:00
Physical Therapist	john doe	f	1000065.0	2024-08-16 16:00:00
Physical Therapist	john doe	f	1000028.0	2024-08-16 16:30:00
Physical Therapist	john doe	f	1000060.0	2024-08-17 09:00:00
Physical Therapist	john doe	t	\N	2024-08-17 09:30:00
Physical Therapist	john doe	t	\N	2024-08-17 10:00:00
Physical Therapist	john doe	t	\N	2024-08-17 10:30:00
Physical Therapist	john doe	t	\N	2024-08-17 11:00:00
Physical Therapist	john doe	t	\N	2024-08-17 11:30:00
Physical Therapist	john doe	f	1000062.0	2024-08-17 12:00:00
Physical Therapist	john doe	t	\N	2024-08-17 12:30:00
Physical Therapist	john doe	t	\N	2024-08-19 08:00:00
Physical Therapist	john doe	t	\N	2024-08-19 08:30:00
Physical Therapist	john doe	t	\N	2024-08-19 09:00:00
Physical Therapist	john doe	t	\N	2024-08-19 09:30:00
Physical Therapist	john doe	t	\N	2024-08-19 10:00:00
Physical Therapist	john doe	f	1000040.0	2024-08-19 10:30:00
Physical Therapist	john doe	t	\N	2024-08-19 11:00:00
Physical Therapist	john doe	t	\N	2024-08-19 11:30:00
Physical Therapist	john doe	f	1000088.0	2024-08-19 12:00:00
Physical Therapist	john doe	t	\N	2024-08-19 12:30:00
Physical Therapist	john doe	t	\N	2024-08-19 13:00:00
Physical Therapist	john doe	f	1000096.0	2024-08-19 13:30:00
Physical Therapist	john doe	f	1000015.0	2024-08-19 14:00:00
Physical Therapist	john doe	f	1000077.0	2024-08-19 14:30:00
Physical Therapist	john doe	t	\N	2024-08-19 15:00:00
Physical Therapist	john doe	t	\N	2024-08-19 15:30:00
Physical Therapist	john doe	t	\N	2024-08-19 16:00:00
Physical Therapist	john doe	f	1000099.0	2024-08-19 16:30:00
Physical Therapist	john doe	t	\N	2024-08-20 08:00:00
Physical Therapist	john doe	f	1000073.0	2024-08-20 08:30:00
Physical Therapist	john doe	t	\N	2024-08-20 09:00:00
Physical Therapist	john doe	f	1000047.0	2024-08-20 09:30:00
Physical Therapist	john doe	t	\N	2024-08-20 10:00:00
Physical Therapist	john doe	f	1000100.0	2024-08-20 10:30:00
Physical Therapist	john doe	t	\N	2024-08-20 11:00:00
Physical Therapist	john doe	t	\N	2024-08-20 11:30:00
Physical Therapist	john doe	t	\N	2024-08-20 12:00:00
Physical Therapist	john doe	f	1000055.0	2024-08-20 12:30:00
Physical Therapist	john doe	t	\N	2024-08-20 13:00:00
Physical Therapist	john doe	t	\N	2024-08-20 13:30:00
Physical Therapist	john doe	f	1000032.0	2024-08-20 14:00:00
Physical Therapist	john doe	t	\N	2024-08-20 14:30:00
Physical Therapist	john doe	f	1000074.0	2024-08-20 15:00:00
Physical Therapist	john doe	t	\N	2024-08-20 15:30:00
Physical Therapist	john doe	t	\N	2024-08-20 16:00:00
Physical Therapist	john doe	f	1000092.0	2024-08-20 16:30:00
Physical Therapist	john doe	t	\N	2024-08-21 08:00:00
Physical Therapist	john doe	f	1000015.0	2024-08-21 08:30:00
Physical Therapist	john doe	t	\N	2024-08-21 09:00:00
Physical Therapist	john doe	t	\N	2024-08-21 09:30:00
Physical Therapist	john doe	t	\N	2024-08-21 10:00:00
Physical Therapist	john doe	t	\N	2024-08-21 10:30:00
Physical Therapist	john doe	t	\N	2024-08-21 11:00:00
Physical Therapist	john doe	t	\N	2024-08-21 11:30:00
Physical Therapist	john doe	t	\N	2024-08-21 12:00:00
Physical Therapist	john doe	f	1000069.0	2024-08-21 12:30:00
Physical Therapist	john doe	f	1000037.0	2024-08-21 13:00:00
Physical Therapist	john doe	t	\N	2024-08-21 13:30:00
Physical Therapist	john doe	t	\N	2024-08-21 14:00:00
Physical Therapist	john doe	f	1000000.0	2024-08-21 14:30:00
Physical Therapist	john doe	t	\N	2024-08-21 15:00:00
Physical Therapist	john doe	f	1000046.0	2024-08-21 15:30:00
Physical Therapist	john doe	t	\N	2024-08-21 16:00:00
Physical Therapist	john doe	t	\N	2024-08-21 16:30:00
Physical Therapist	john doe	f	1000026.0	2024-08-22 08:00:00
Physical Therapist	john doe	t	\N	2024-08-22 08:30:00
Physical Therapist	john doe	t	\N	2024-08-22 09:00:00
Physical Therapist	john doe	f	1000038.0	2024-08-22 09:30:00
Physical Therapist	john doe	t	\N	2024-08-22 10:00:00
Physical Therapist	john doe	t	\N	2024-08-22 10:30:00
Physical Therapist	john doe	t	\N	2024-08-22 11:00:00
Physical Therapist	john doe	f	1000048.0	2024-08-22 11:30:00
Physical Therapist	john doe	t	\N	2024-08-22 12:00:00
Physical Therapist	john doe	f	1000099.0	2024-08-22 12:30:00
Physical Therapist	john doe	t	\N	2024-08-22 13:00:00
Physical Therapist	john doe	f	1000073.0	2024-08-22 13:30:00
Physical Therapist	john doe	f	1000011.0	2024-08-22 14:00:00
Physical Therapist	john doe	t	\N	2024-08-22 14:30:00
Physical Therapist	john doe	f	1000065.0	2024-08-22 15:00:00
Physical Therapist	john doe	t	\N	2024-08-22 15:30:00
Physical Therapist	john doe	t	\N	2024-08-22 16:00:00
Physical Therapist	john doe	t	\N	2024-08-22 16:30:00
Physical Therapist	john doe	f	1000009.0	2024-08-23 08:00:00
Physical Therapist	john doe	t	\N	2024-08-23 08:30:00
Physical Therapist	john doe	f	1000079.0	2024-08-23 09:00:00
Physical Therapist	john doe	t	\N	2024-08-23 09:30:00
Physical Therapist	john doe	f	1000025.0	2024-08-23 10:00:00
Physical Therapist	john doe	t	\N	2024-08-23 10:30:00
Physical Therapist	john doe	t	\N	2024-08-23 11:00:00
Physical Therapist	john doe	f	1000098.0	2024-08-23 11:30:00
Physical Therapist	john doe	t	\N	2024-08-23 12:00:00
Physical Therapist	john doe	t	\N	2024-08-23 12:30:00
Physical Therapist	john doe	f	1000033.0	2024-08-23 13:00:00
Physical Therapist	john doe	t	\N	2024-08-23 13:30:00
Physical Therapist	john doe	f	1000089.0	2024-08-23 14:00:00
Physical Therapist	john doe	t	\N	2024-08-23 14:30:00
Physical Therapist	john doe	t	\N	2024-08-23 15:00:00
Physical Therapist	john doe	t	\N	2024-08-23 15:30:00
Physical Therapist	john doe	t	\N	2024-08-23 16:00:00
Physical Therapist	john doe	t	\N	2024-08-23 16:30:00
Physical Therapist	john doe	t	\N	2024-08-24 09:00:00
Physical Therapist	john doe	t	\N	2024-08-24 09:30:00
Physical Therapist	john doe	t	\N	2024-08-24 10:00:00
Physical Therapist	john doe	t	\N	2024-08-24 10:30:00
Physical Therapist	john doe	t	\N	2024-08-24 11:00:00
Physical Therapist	john doe	f	1000055.0	2024-08-24 11:30:00
Physical Therapist	john doe	f	1000001.0	2024-08-24 12:00:00
Physical Therapist	john doe	f	1000028.0	2024-08-24 12:30:00
Physical Therapist	john doe	t	\N	2024-08-26 08:00:00
Physical Therapist	john doe	t	\N	2024-08-26 08:30:00
Physical Therapist	john doe	t	\N	2024-08-26 09:00:00
Physical Therapist	john doe	f	1000063.0	2024-08-26 09:30:00
Physical Therapist	john doe	t	\N	2024-08-26 10:00:00
Physical Therapist	john doe	t	\N	2024-08-26 10:30:00
Physical Therapist	john doe	f	1000080.0	2024-08-26 11:00:00
Physical Therapist	john doe	t	\N	2024-08-26 11:30:00
Physical Therapist	john doe	f	1000059.0	2024-08-26 12:00:00
Physical Therapist	john doe	t	\N	2024-08-26 12:30:00
Physical Therapist	john doe	f	1000014.0	2024-08-26 13:00:00
Physical Therapist	john doe	t	\N	2024-08-26 13:30:00
Physical Therapist	john doe	t	\N	2024-08-26 14:00:00
Physical Therapist	john doe	t	\N	2024-08-26 14:30:00
Physical Therapist	john doe	f	1000048.0	2024-08-26 15:00:00
Physical Therapist	john doe	f	1000090.0	2024-08-26 15:30:00
Physical Therapist	john doe	t	\N	2024-08-26 16:00:00
Physical Therapist	john doe	t	\N	2024-08-26 16:30:00
Physical Therapist	john doe	t	\N	2024-08-27 08:00:00
Physical Therapist	john doe	f	1000034.0	2024-08-27 08:30:00
Physical Therapist	john doe	t	\N	2024-08-27 09:00:00
Physical Therapist	john doe	f	1000038.0	2024-08-27 09:30:00
Physical Therapist	john doe	f	1000077.0	2024-08-27 10:00:00
Physical Therapist	john doe	t	\N	2024-08-27 10:30:00
Physical Therapist	john doe	t	\N	2024-08-27 11:00:00
Physical Therapist	john doe	f	1000071.0	2024-08-27 11:30:00
Physical Therapist	john doe	t	\N	2024-08-27 12:00:00
Physical Therapist	john doe	f	1000019.0	2024-08-27 12:30:00
Physical Therapist	john doe	f	1000091.0	2024-08-27 13:00:00
Physical Therapist	john doe	t	\N	2024-08-27 13:30:00
Physical Therapist	john doe	f	1000040.0	2024-08-27 14:00:00
Physical Therapist	john doe	t	\N	2024-08-27 14:30:00
Physical Therapist	john doe	f	1000016.0	2024-08-27 15:00:00
Physical Therapist	john doe	f	1000034.0	2024-08-27 15:30:00
Physical Therapist	john doe	t	\N	2024-08-27 16:00:00
Physical Therapist	john doe	t	\N	2024-08-27 16:30:00
Physical Therapist	john doe	f	1000066.0	2024-08-28 08:00:00
Physical Therapist	john doe	t	\N	2024-08-28 08:30:00
Physical Therapist	john doe	t	\N	2024-08-28 09:00:00
Physical Therapist	john doe	f	1000043.0	2024-08-28 09:30:00
Physical Therapist	john doe	f	1000095.0	2024-08-28 10:00:00
Physical Therapist	john doe	t	\N	2024-08-28 10:30:00
Physical Therapist	john doe	f	1000089.0	2024-08-28 11:00:00
Physical Therapist	john doe	f	1000073.0	2024-08-28 11:30:00
Physical Therapist	john doe	t	\N	2024-08-28 12:00:00
Physical Therapist	john doe	f	1000052.0	2024-08-28 12:30:00
Physical Therapist	john doe	t	\N	2024-08-28 13:00:00
Physical Therapist	john doe	f	1000065.0	2024-08-28 13:30:00
Physical Therapist	john doe	t	\N	2024-08-28 14:00:00
Physical Therapist	john doe	f	1000030.0	2024-08-28 14:30:00
Physical Therapist	john doe	t	\N	2024-08-28 15:00:00
Physical Therapist	john doe	t	\N	2024-08-28 15:30:00
Physical Therapist	john doe	f	1000058.0	2024-08-28 16:00:00
Physical Therapist	john doe	t	\N	2024-08-28 16:30:00
Physical Therapist	john doe	f	1000041.0	2024-08-29 08:00:00
Physical Therapist	john doe	f	1000000.0	2024-08-29 08:30:00
Physical Therapist	john doe	f	1000077.0	2024-08-29 09:00:00
Physical Therapist	john doe	f	1000040.0	2024-08-29 09:30:00
Physical Therapist	john doe	t	\N	2024-08-29 10:00:00
Physical Therapist	john doe	f	1000032.0	2024-08-29 10:30:00
Physical Therapist	john doe	f	1000085.0	2024-08-29 11:00:00
Physical Therapist	john doe	t	\N	2024-08-29 11:30:00
Physical Therapist	john doe	t	\N	2024-08-29 12:00:00
Physical Therapist	john doe	t	\N	2024-08-29 12:30:00
Physical Therapist	john doe	t	\N	2024-08-29 13:00:00
Physical Therapist	john doe	f	1000070.0	2024-08-29 13:30:00
Physical Therapist	john doe	t	\N	2024-08-29 14:00:00
Physical Therapist	john doe	t	\N	2024-08-29 14:30:00
Physical Therapist	john doe	t	\N	2024-08-29 15:00:00
Physical Therapist	john doe	t	\N	2024-08-29 15:30:00
Physical Therapist	john doe	t	\N	2024-08-29 16:00:00
Physical Therapist	john doe	t	\N	2024-08-29 16:30:00
Physical Therapist	john doe	f	1000092.0	2024-08-30 08:00:00
Physical Therapist	john doe	t	\N	2024-08-30 08:30:00
Physical Therapist	john doe	t	\N	2024-08-30 09:00:00
Physical Therapist	john doe	f	1000049.0	2024-08-30 09:30:00
Physical Therapist	john doe	t	\N	2024-08-30 10:00:00
Physical Therapist	john doe	t	\N	2024-08-30 10:30:00
Physical Therapist	john doe	t	\N	2024-08-30 11:00:00
Physical Therapist	john doe	t	\N	2024-08-30 11:30:00
Physical Therapist	john doe	t	\N	2024-08-30 12:00:00
Physical Therapist	john doe	f	1000044.0	2024-08-30 12:30:00
Physical Therapist	john doe	t	\N	2024-08-30 13:00:00
Physical Therapist	john doe	t	\N	2024-08-30 13:30:00
Physical Therapist	john doe	t	\N	2024-08-30 14:00:00
Physical Therapist	john doe	t	\N	2024-08-30 14:30:00
Physical Therapist	john doe	t	\N	2024-08-30 15:00:00
Physical Therapist	john doe	f	1000067.0	2024-08-30 15:30:00
Physical Therapist	john doe	t	\N	2024-08-30 16:00:00
Physical Therapist	john doe	t	\N	2024-08-30 16:30:00
Physical Therapist	john doe	t	\N	2024-08-31 09:00:00
Physical Therapist	john doe	t	\N	2024-08-31 09:30:00
Physical Therapist	john doe	t	\N	2024-08-31 10:00:00
Physical Therapist	john doe	t	\N	2024-08-31 10:30:00
Physical Therapist	john doe	f	1000057.0	2024-08-31 11:00:00
Physical Therapist	john doe	t	\N	2024-08-31 11:30:00
Physical Therapist	john doe	t	\N	2024-08-31 12:00:00
Physical Therapist	john doe	t	\N	2024-08-31 12:30:00
Physical Therapist	john doe	t	\N	2024-09-02 08:00:00
Physical Therapist	john doe	t	\N	2024-09-02 08:30:00
Physical Therapist	john doe	t	\N	2024-09-02 09:00:00
Physical Therapist	john doe	t	\N	2024-09-02 09:30:00
Physical Therapist	john doe	t	\N	2024-09-02 10:00:00
Physical Therapist	john doe	t	\N	2024-09-02 10:30:00
Physical Therapist	john doe	f	1000063.0	2024-09-02 11:00:00
Physical Therapist	john doe	t	\N	2024-09-02 11:30:00
Physical Therapist	john doe	t	\N	2024-09-02 12:00:00
Physical Therapist	john doe	t	\N	2024-09-02 12:30:00
Physical Therapist	john doe	t	\N	2024-09-02 13:00:00
Physical Therapist	john doe	t	\N	2024-09-02 13:30:00
Physical Therapist	john doe	f	1000080.0	2024-09-02 14:00:00
Physical Therapist	john doe	f	1000034.0	2024-09-02 14:30:00
Physical Therapist	john doe	t	\N	2024-09-02 15:00:00
Physical Therapist	john doe	t	\N	2024-09-02 15:30:00
Physical Therapist	john doe	f	1000015.0	2024-09-02 16:00:00
Physical Therapist	john doe	t	\N	2024-09-02 16:30:00
Physical Therapist	john doe	f	1000086.0	2024-09-03 08:00:00
Physical Therapist	john doe	t	\N	2024-09-03 08:30:00
Physical Therapist	john doe	f	1000074.0	2024-09-03 09:00:00
Physical Therapist	john doe	f	1000047.0	2024-09-03 09:30:00
Physical Therapist	john doe	t	\N	2024-09-03 10:00:00
Physical Therapist	john doe	t	\N	2024-09-03 10:30:00
Physical Therapist	john doe	t	\N	2024-09-03 11:00:00
Physical Therapist	john doe	t	\N	2024-09-03 11:30:00
Physical Therapist	john doe	t	\N	2024-09-03 12:00:00
Physical Therapist	john doe	f	1000090.0	2024-09-03 12:30:00
Physical Therapist	john doe	t	\N	2024-09-03 13:00:00
Physical Therapist	john doe	t	\N	2024-09-03 13:30:00
Physical Therapist	john doe	t	\N	2024-09-03 14:00:00
Physical Therapist	john doe	t	\N	2024-09-03 14:30:00
Physical Therapist	john doe	t	\N	2024-09-03 15:00:00
Physical Therapist	john doe	f	1000096.0	2024-09-03 15:30:00
Physical Therapist	john doe	f	1000033.0	2024-09-03 16:00:00
Physical Therapist	john doe	t	\N	2024-09-03 16:30:00
Pharmacist	michael green	t	\N	2024-08-22 16:30:00
Pharmacist	michael green	t	\N	2024-08-23 08:00:00
Pharmacist	michael green	t	\N	2024-08-23 08:30:00
Pharmacist	michael green	t	\N	2024-08-23 09:00:00
Pharmacist	michael green	t	\N	2024-08-23 09:30:00
Pharmacist	michael green	f	1000095.0	2024-08-23 10:00:00
Pharmacist	michael green	t	\N	2024-08-23 10:30:00
Pharmacist	michael green	t	\N	2024-08-23 11:00:00
Pharmacist	michael green	f	1000004.0	2024-08-23 11:30:00
Pharmacist	michael green	t	\N	2024-08-23 12:00:00
Pharmacist	michael green	t	\N	2024-08-23 12:30:00
Pharmacist	michael green	t	\N	2024-08-23 13:00:00
Pharmacist	michael green	t	\N	2024-08-23 13:30:00
Pharmacist	michael green	f	1000070.0	2024-08-23 14:00:00
Pharmacist	michael green	t	\N	2024-08-23 14:30:00
Pharmacist	michael green	f	1000069.0	2024-08-23 15:00:00
Pharmacist	michael green	t	\N	2024-08-23 15:30:00
Pharmacist	michael green	t	\N	2024-08-23 16:00:00
Pharmacist	michael green	f	1000092.0	2024-08-23 16:30:00
Pharmacist	michael green	f	1000006.0	2024-08-24 09:00:00
Pharmacist	michael green	t	\N	2024-08-24 09:30:00
Pharmacist	michael green	t	\N	2024-08-24 10:00:00
Pharmacist	michael green	t	\N	2024-08-24 10:30:00
Pharmacist	michael green	t	\N	2024-08-24 11:00:00
Pharmacist	michael green	t	\N	2024-08-24 11:30:00
Pharmacist	michael green	t	\N	2024-08-24 12:00:00
Pharmacist	michael green	f	1000071.0	2024-08-24 12:30:00
Pharmacist	michael green	f	1000032.0	2024-08-26 08:00:00
Social Worker	emily johnson	f	1000040.0	2024-08-05 16:00:00
Social Worker	emily johnson	f	1000073.0	2024-08-05 16:30:00
Social Worker	emily johnson	f	1000078.0	2024-08-06 08:00:00
Social Worker	emily johnson	f	1000071.0	2024-08-06 08:30:00
Social Worker	emily johnson	f	1000044.0	2024-08-06 09:00:00
Social Worker	emily johnson	f	1000047.0	2024-08-06 09:30:00
Social Worker	emily johnson	f	1000057.0	2024-08-06 10:00:00
Social Worker	emily johnson	f	1000011.0	2024-08-06 10:30:00
Social Worker	emily johnson	f	1000084.0	2024-08-06 11:00:00
Social Worker	emily johnson	f	1000002.0	2024-08-06 11:30:00
Social Worker	emily johnson	f	1000068.0	2024-08-06 12:00:00
Social Worker	emily johnson	f	1000074.0	2024-08-06 12:30:00
Social Worker	emily johnson	f	1000004.0	2024-08-06 13:00:00
Social Worker	emily johnson	f	1000045.0	2024-08-06 13:30:00
Social Worker	emily johnson	f	1000012.0	2024-08-06 14:00:00
Social Worker	emily johnson	f	1000048.0	2024-08-06 14:30:00
Social Worker	emily johnson	f	1000092.0	2024-08-06 15:00:00
Social Worker	emily johnson	f	1000045.0	2024-08-06 15:30:00
Social Worker	emily johnson	f	1000038.0	2024-08-06 16:00:00
Social Worker	emily johnson	f	1000089.0	2024-08-06 16:30:00
Social Worker	emily johnson	t	\N	2024-08-07 08:00:00
Social Worker	emily johnson	t	\N	2024-08-07 08:30:00
Social Worker	emily johnson	t	\N	2024-08-07 09:00:00
Social Worker	emily johnson	t	\N	2024-08-07 09:30:00
Social Worker	emily johnson	f	1000046.0	2024-08-07 10:00:00
Social Worker	emily johnson	t	\N	2024-08-07 10:30:00
Social Worker	emily johnson	f	1000090.0	2024-08-07 11:00:00
Social Worker	emily johnson	t	\N	2024-08-07 11:30:00
Social Worker	emily johnson	t	\N	2024-08-07 12:00:00
Social Worker	emily johnson	f	1000024.0	2024-08-07 12:30:00
Social Worker	emily johnson	t	\N	2024-08-07 13:00:00
Social Worker	emily johnson	t	\N	2024-08-07 13:30:00
Social Worker	emily johnson	f	1000029.0	2024-08-07 14:00:00
Social Worker	emily johnson	t	\N	2024-08-07 14:30:00
Social Worker	emily johnson	f	1000002.0	2024-08-07 15:00:00
Social Worker	emily johnson	t	\N	2024-08-07 15:30:00
Social Worker	emily johnson	t	\N	2024-08-07 16:00:00
Social Worker	emily johnson	f	1000012.0	2024-08-07 16:30:00
Social Worker	emily johnson	t	\N	2024-08-08 08:00:00
Social Worker	emily johnson	t	\N	2024-08-08 08:30:00
Social Worker	emily johnson	f	1000005.0	2024-08-08 09:00:00
Social Worker	emily johnson	f	1000041.0	2024-08-08 09:30:00
Social Worker	emily johnson	t	\N	2024-08-08 10:00:00
Social Worker	emily johnson	t	\N	2024-08-08 10:30:00
Social Worker	emily johnson	t	\N	2024-08-08 11:00:00
Social Worker	emily johnson	t	\N	2024-08-08 11:30:00
Social Worker	emily johnson	t	\N	2024-08-08 12:00:00
Social Worker	emily johnson	t	\N	2024-08-08 12:30:00
Social Worker	emily johnson	f	1000026.0	2024-08-08 13:00:00
Social Worker	emily johnson	t	\N	2024-08-08 13:30:00
Social Worker	emily johnson	f	1000095.0	2024-08-08 14:00:00
Social Worker	emily johnson	t	\N	2024-08-08 14:30:00
Social Worker	emily johnson	f	1000009.0	2024-08-08 15:00:00
Social Worker	emily johnson	t	\N	2024-08-08 15:30:00
Social Worker	emily johnson	f	1000069.0	2024-08-08 16:00:00
Social Worker	emily johnson	t	\N	2024-08-08 16:30:00
Social Worker	emily johnson	f	1000049.0	2024-08-09 08:00:00
Social Worker	emily johnson	t	\N	2024-08-09 08:30:00
Social Worker	emily johnson	f	1000079.0	2024-08-09 09:00:00
Social Worker	emily johnson	t	\N	2024-08-09 09:30:00
Social Worker	emily johnson	t	\N	2024-08-09 10:00:00
Social Worker	emily johnson	t	\N	2024-08-09 10:30:00
Social Worker	emily johnson	t	\N	2024-08-09 11:00:00
Social Worker	emily johnson	t	\N	2024-08-09 11:30:00
Social Worker	emily johnson	t	\N	2024-08-09 12:00:00
Social Worker	emily johnson	f	1000049.0	2024-08-09 12:30:00
Social Worker	emily johnson	t	\N	2024-08-09 13:00:00
Social Worker	emily johnson	t	\N	2024-08-09 13:30:00
Social Worker	emily johnson	t	\N	2024-08-09 14:00:00
Social Worker	emily johnson	t	\N	2024-08-09 14:30:00
Social Worker	emily johnson	t	\N	2024-08-09 15:00:00
Social Worker	emily johnson	f	1000082.0	2024-08-09 15:30:00
Social Worker	emily johnson	t	\N	2024-08-09 16:00:00
Social Worker	emily johnson	f	1000100.0	2024-08-09 16:30:00
Social Worker	emily johnson	f	1000005.0	2024-08-10 09:00:00
Social Worker	emily johnson	t	\N	2024-08-10 09:30:00
Social Worker	emily johnson	t	\N	2024-08-10 10:00:00
Social Worker	emily johnson	t	\N	2024-08-10 10:30:00
Social Worker	emily johnson	t	\N	2024-08-10 11:00:00
Social Worker	emily johnson	t	\N	2024-08-10 11:30:00
Social Worker	emily johnson	t	\N	2024-08-10 12:00:00
Social Worker	emily johnson	f	1000022.0	2024-08-10 12:30:00
Social Worker	emily johnson	f	1000095.0	2024-08-12 08:00:00
Geriatrician	daniel miller	t	\N	2024-09-03 11:00:00
Geriatrician	daniel miller	t	\N	2024-09-03 11:30:00
Geriatrician	daniel miller	t	\N	2024-09-03 12:00:00
Geriatrician	daniel miller	t	\N	2024-09-03 12:30:00
Geriatrician	daniel miller	t	\N	2024-09-03 13:00:00
Geriatrician	daniel miller	t	\N	2024-09-03 13:30:00
Geriatrician	daniel miller	t	\N	2024-09-03 14:00:00
Geriatrician	daniel miller	t	\N	2024-09-03 14:30:00
Geriatrician	daniel miller	t	\N	2024-09-03 15:00:00
Geriatrician	daniel miller	f	1000056.0	2024-09-03 15:30:00
Geriatrician	daniel miller	t	\N	2024-09-03 16:00:00
Geriatrician	daniel miller	t	\N	2024-09-03 16:30:00
Social Worker	emily johnson	f	1000014.0	2024-08-12 08:30:00
Social Worker	emily johnson	t	\N	2024-08-12 09:00:00
Social Worker	emily johnson	t	\N	2024-08-12 09:30:00
Social Worker	emily johnson	t	\N	2024-08-12 10:00:00
Social Worker	emily johnson	t	\N	2024-08-12 10:30:00
Social Worker	emily johnson	f	1000020.0	2024-08-12 11:00:00
Social Worker	emily johnson	f	1000017.0	2024-08-12 11:30:00
Social Worker	emily johnson	t	\N	2024-08-12 12:00:00
Social Worker	emily johnson	t	\N	2024-08-12 12:30:00
Social Worker	emily johnson	f	1000089.0	2024-08-12 13:00:00
Social Worker	emily johnson	t	\N	2024-08-12 13:30:00
Social Worker	emily johnson	t	\N	2024-08-12 14:00:00
Social Worker	emily johnson	t	\N	2024-08-12 14:30:00
Social Worker	emily johnson	t	\N	2024-08-12 15:00:00
Social Worker	emily johnson	t	\N	2024-08-12 15:30:00
Social Worker	emily johnson	t	\N	2024-08-12 16:00:00
Social Worker	emily johnson	t	\N	2024-08-12 16:30:00
Social Worker	emily johnson	f	1000054.0	2024-08-13 08:00:00
Social Worker	emily johnson	t	\N	2024-08-13 08:30:00
Social Worker	emily johnson	f	1000004.0	2024-08-13 09:00:00
Social Worker	emily johnson	t	\N	2024-08-13 09:30:00
Social Worker	emily johnson	t	\N	2024-08-13 10:00:00
Social Worker	emily johnson	t	\N	2024-08-13 10:30:00
Social Worker	emily johnson	t	\N	2024-08-13 11:00:00
Social Worker	emily johnson	t	\N	2024-08-13 11:30:00
Social Worker	emily johnson	f	1000020.0	2024-08-13 12:00:00
Social Worker	emily johnson	t	\N	2024-08-13 12:30:00
Social Worker	emily johnson	t	\N	2024-08-13 13:00:00
Social Worker	emily johnson	t	\N	2024-08-13 13:30:00
Social Worker	emily johnson	f	1000035.0	2024-08-13 14:00:00
Social Worker	emily johnson	t	\N	2024-08-13 14:30:00
Social Worker	emily johnson	t	\N	2024-08-13 15:00:00
Social Worker	emily johnson	f	1000042.0	2024-08-13 15:30:00
Social Worker	emily johnson	t	\N	2024-08-13 16:00:00
Social Worker	emily johnson	t	\N	2024-08-13 16:30:00
Social Worker	emily johnson	t	\N	2024-08-14 08:00:00
Social Worker	emily johnson	t	\N	2024-08-14 08:30:00
Social Worker	emily johnson	t	\N	2024-08-14 09:00:00
Social Worker	emily johnson	t	\N	2024-08-14 09:30:00
Social Worker	emily johnson	f	1000016.0	2024-08-14 10:00:00
Social Worker	emily johnson	t	\N	2024-08-14 10:30:00
Social Worker	emily johnson	t	\N	2024-08-14 11:00:00
Social Worker	emily johnson	t	\N	2024-08-14 11:30:00
Social Worker	emily johnson	t	\N	2024-08-14 12:00:00
Social Worker	emily johnson	f	1000007.0	2024-08-14 12:30:00
Social Worker	emily johnson	t	\N	2024-08-14 13:00:00
Social Worker	emily johnson	t	\N	2024-08-14 13:30:00
Social Worker	emily johnson	f	1000089.0	2024-08-14 14:00:00
Social Worker	emily johnson	t	\N	2024-08-14 14:30:00
Social Worker	emily johnson	t	\N	2024-08-14 15:00:00
Social Worker	emily johnson	f	1000001.0	2024-08-14 15:30:00
Social Worker	emily johnson	t	\N	2024-08-14 16:00:00
Social Worker	emily johnson	f	1000095.0	2024-08-14 16:30:00
Social Worker	emily johnson	f	1000078.0	2024-08-15 08:00:00
Social Worker	emily johnson	t	\N	2024-08-15 08:30:00
Social Worker	emily johnson	t	\N	2024-08-15 09:00:00
Social Worker	emily johnson	t	\N	2024-08-15 09:30:00
Social Worker	emily johnson	t	\N	2024-08-15 10:00:00
Social Worker	emily johnson	f	1000054.0	2024-08-15 10:30:00
Social Worker	emily johnson	f	1000064.0	2024-08-15 11:00:00
Social Worker	emily johnson	t	\N	2024-08-15 11:30:00
Social Worker	emily johnson	t	\N	2024-08-15 12:00:00
Social Worker	emily johnson	t	\N	2024-08-15 12:30:00
Social Worker	emily johnson	t	\N	2024-08-15 13:00:00
Social Worker	emily johnson	t	\N	2024-08-15 13:30:00
Social Worker	emily johnson	t	\N	2024-08-15 14:00:00
Social Worker	emily johnson	t	\N	2024-08-15 14:30:00
Social Worker	emily johnson	t	\N	2024-08-15 15:00:00
Social Worker	emily johnson	t	\N	2024-08-15 15:30:00
Social Worker	emily johnson	t	\N	2024-08-15 16:00:00
Social Worker	emily johnson	f	1000053.0	2024-08-15 16:30:00
Social Worker	emily johnson	t	\N	2024-08-16 08:00:00
Social Worker	emily johnson	f	1000093.0	2024-08-16 08:30:00
Social Worker	emily johnson	f	1000070.0	2024-08-16 09:00:00
Social Worker	emily johnson	f	1000018.0	2024-08-16 09:30:00
Social Worker	emily johnson	t	\N	2024-08-16 10:00:00
Social Worker	emily johnson	f	1000080.0	2024-08-16 10:30:00
Social Worker	emily johnson	t	\N	2024-08-16 11:00:00
Social Worker	emily johnson	t	\N	2024-08-16 11:30:00
Social Worker	emily johnson	t	\N	2024-08-16 12:00:00
Social Worker	emily johnson	f	1000048.0	2024-08-16 12:30:00
Social Worker	emily johnson	f	1000046.0	2024-08-16 13:00:00
Social Worker	emily johnson	t	\N	2024-08-16 13:30:00
Social Worker	emily johnson	t	\N	2024-08-16 14:00:00
Social Worker	emily johnson	t	\N	2024-08-16 14:30:00
Social Worker	emily johnson	t	\N	2024-08-16 15:00:00
Social Worker	emily johnson	t	\N	2024-08-16 15:30:00
Social Worker	emily johnson	t	\N	2024-08-16 16:00:00
Social Worker	emily johnson	t	\N	2024-08-16 16:30:00
Social Worker	emily johnson	t	\N	2024-08-17 09:00:00
Social Worker	emily johnson	f	1000010.0	2024-08-17 09:30:00
Social Worker	emily johnson	t	\N	2024-08-17 10:00:00
Social Worker	emily johnson	t	\N	2024-08-17 10:30:00
Social Worker	emily johnson	f	1000070.0	2024-08-17 11:00:00
Social Worker	emily johnson	f	1000091.0	2024-08-17 11:30:00
Social Worker	emily johnson	f	1000082.0	2024-08-17 12:00:00
Social Worker	emily johnson	t	\N	2024-08-17 12:30:00
Social Worker	emily johnson	t	\N	2024-08-19 08:00:00
Social Worker	emily johnson	t	\N	2024-08-19 08:30:00
Social Worker	emily johnson	f	1000060.0	2024-08-19 09:00:00
Social Worker	emily johnson	f	1000022.0	2024-08-19 09:30:00
Social Worker	emily johnson	t	\N	2024-08-19 10:00:00
Social Worker	emily johnson	f	1000008.0	2024-08-19 10:30:00
Social Worker	emily johnson	t	\N	2024-08-19 11:00:00
Social Worker	emily johnson	f	1000021.0	2024-08-19 11:30:00
Social Worker	emily johnson	t	\N	2024-08-19 12:00:00
Social Worker	emily johnson	t	\N	2024-08-19 12:30:00
Social Worker	emily johnson	t	\N	2024-08-19 13:00:00
Social Worker	emily johnson	t	\N	2024-08-19 13:30:00
Social Worker	emily johnson	f	1000081.0	2024-08-19 14:00:00
Social Worker	emily johnson	f	1000049.0	2024-08-19 14:30:00
Social Worker	emily johnson	t	\N	2024-08-19 15:00:00
Social Worker	emily johnson	t	\N	2024-08-19 15:30:00
Social Worker	emily johnson	t	\N	2024-08-19 16:00:00
Social Worker	emily johnson	t	\N	2024-08-19 16:30:00
Social Worker	emily johnson	t	\N	2024-08-20 08:00:00
Social Worker	emily johnson	t	\N	2024-08-20 08:30:00
Social Worker	emily johnson	t	\N	2024-08-20 09:00:00
Social Worker	emily johnson	t	\N	2024-08-20 09:30:00
Social Worker	emily johnson	t	\N	2024-08-20 10:00:00
Social Worker	emily johnson	t	\N	2024-08-20 10:30:00
Social Worker	emily johnson	f	1000032.0	2024-08-20 11:00:00
Social Worker	emily johnson	t	\N	2024-08-20 11:30:00
Social Worker	emily johnson	t	\N	2024-08-20 12:00:00
Social Worker	emily johnson	t	\N	2024-08-20 12:30:00
Social Worker	emily johnson	t	\N	2024-08-20 13:00:00
Social Worker	emily johnson	t	\N	2024-08-20 13:30:00
Social Worker	emily johnson	f	1000062.0	2024-08-20 14:00:00
Social Worker	emily johnson	f	1000091.0	2024-08-20 14:30:00
Social Worker	emily johnson	f	1000046.0	2024-08-20 15:00:00
Social Worker	emily johnson	t	\N	2024-08-20 15:30:00
Social Worker	emily johnson	f	1000004.0	2024-08-20 16:00:00
Social Worker	emily johnson	f	1000005.0	2024-08-20 16:30:00
Social Worker	emily johnson	f	1000028.0	2024-08-21 08:00:00
Social Worker	emily johnson	f	1000029.0	2024-08-21 08:30:00
Social Worker	emily johnson	t	\N	2024-08-21 09:00:00
Social Worker	emily johnson	t	\N	2024-08-21 09:30:00
Social Worker	emily johnson	t	\N	2024-08-21 10:00:00
Social Worker	emily johnson	t	\N	2024-08-21 10:30:00
Social Worker	emily johnson	f	1000082.0	2024-08-21 11:00:00
Social Worker	emily johnson	t	\N	2024-08-21 11:30:00
Social Worker	emily johnson	t	\N	2024-08-21 12:00:00
Social Worker	emily johnson	f	1000025.0	2024-08-21 12:30:00
Social Worker	emily johnson	t	\N	2024-08-21 13:00:00
Social Worker	emily johnson	t	\N	2024-08-21 13:30:00
Social Worker	emily johnson	t	\N	2024-08-21 14:00:00
Social Worker	emily johnson	t	\N	2024-08-21 14:30:00
Social Worker	emily johnson	t	\N	2024-08-21 15:00:00
Social Worker	emily johnson	t	\N	2024-08-21 15:30:00
Social Worker	emily johnson	t	\N	2024-08-21 16:00:00
Social Worker	emily johnson	f	1000059.0	2024-08-21 16:30:00
Social Worker	emily johnson	t	\N	2024-08-22 08:00:00
Social Worker	emily johnson	t	\N	2024-08-22 08:30:00
Social Worker	emily johnson	f	1000067.0	2024-08-22 09:00:00
Social Worker	emily johnson	t	\N	2024-08-22 09:30:00
Social Worker	emily johnson	f	1000045.0	2024-08-22 10:00:00
Social Worker	emily johnson	t	\N	2024-08-22 10:30:00
Social Worker	emily johnson	f	1000099.0	2024-08-22 11:00:00
Social Worker	emily johnson	t	\N	2024-08-22 11:30:00
Social Worker	emily johnson	f	1000038.0	2024-08-22 12:00:00
Social Worker	emily johnson	t	\N	2024-08-22 12:30:00
Social Worker	emily johnson	f	1000029.0	2024-08-22 13:00:00
Social Worker	emily johnson	t	\N	2024-08-22 13:30:00
Social Worker	emily johnson	f	1000028.0	2024-08-22 14:00:00
Social Worker	emily johnson	t	\N	2024-08-22 14:30:00
Social Worker	emily johnson	t	\N	2024-08-22 15:00:00
Social Worker	emily johnson	f	1000027.0	2024-08-22 15:30:00
Social Worker	emily johnson	f	1000032.0	2024-08-22 16:00:00
Social Worker	emily johnson	t	\N	2024-08-22 16:30:00
Social Worker	emily johnson	f	1000045.0	2024-08-23 08:00:00
Social Worker	emily johnson	t	\N	2024-08-23 08:30:00
Social Worker	emily johnson	f	1000099.0	2024-08-23 09:00:00
Social Worker	emily johnson	t	\N	2024-08-23 09:30:00
Social Worker	emily johnson	t	\N	2024-08-23 10:00:00
Social Worker	emily johnson	t	\N	2024-08-23 10:30:00
Social Worker	emily johnson	t	\N	2024-08-23 11:00:00
Social Worker	emily johnson	t	\N	2024-08-23 11:30:00
Social Worker	emily johnson	t	\N	2024-08-23 12:00:00
Social Worker	emily johnson	f	1000006.0	2024-08-23 12:30:00
Social Worker	emily johnson	f	1000030.0	2024-08-23 13:00:00
Social Worker	emily johnson	t	\N	2024-08-23 13:30:00
Social Worker	emily johnson	t	\N	2024-08-23 14:00:00
Social Worker	emily johnson	f	1000087.0	2024-08-23 14:30:00
Social Worker	emily johnson	t	\N	2024-08-23 15:00:00
Social Worker	emily johnson	t	\N	2024-08-23 15:30:00
Social Worker	emily johnson	t	\N	2024-08-23 16:00:00
Social Worker	emily johnson	f	1000056.0	2024-08-23 16:30:00
Social Worker	emily johnson	f	1000001.0	2024-08-24 09:00:00
Social Worker	emily johnson	f	1000046.0	2024-08-24 09:30:00
Social Worker	emily johnson	f	1000090.0	2024-08-24 10:00:00
Social Worker	emily johnson	t	\N	2024-08-24 10:30:00
Social Worker	emily johnson	t	\N	2024-08-24 11:00:00
Social Worker	emily johnson	t	\N	2024-08-24 11:30:00
Social Worker	emily johnson	t	\N	2024-08-24 12:00:00
Social Worker	emily johnson	t	\N	2024-08-24 12:30:00
Social Worker	emily johnson	t	\N	2024-08-26 08:00:00
Social Worker	emily johnson	t	\N	2024-08-26 08:30:00
Social Worker	emily johnson	t	\N	2024-08-26 09:00:00
Social Worker	emily johnson	t	\N	2024-08-26 09:30:00
Social Worker	emily johnson	t	\N	2024-08-26 10:00:00
Social Worker	emily johnson	t	\N	2024-08-26 10:30:00
Social Worker	emily johnson	t	\N	2024-08-26 11:00:00
Social Worker	emily johnson	t	\N	2024-08-26 11:30:00
Social Worker	emily johnson	t	\N	2024-08-26 12:00:00
Social Worker	emily johnson	t	\N	2024-08-26 12:30:00
Social Worker	emily johnson	f	1000038.0	2024-08-26 13:00:00
Social Worker	emily johnson	f	1000012.0	2024-08-26 13:30:00
Social Worker	emily johnson	t	\N	2024-08-26 14:00:00
Social Worker	emily johnson	t	\N	2024-08-26 14:30:00
Social Worker	emily johnson	f	1000048.0	2024-08-26 15:00:00
Social Worker	emily johnson	t	\N	2024-08-26 15:30:00
Social Worker	emily johnson	t	\N	2024-08-26 16:00:00
Social Worker	emily johnson	t	\N	2024-08-26 16:30:00
Social Worker	emily johnson	t	\N	2024-08-27 08:00:00
Social Worker	emily johnson	t	\N	2024-08-27 08:30:00
Social Worker	emily johnson	t	\N	2024-08-27 09:00:00
Social Worker	emily johnson	f	1000091.0	2024-08-27 09:30:00
Social Worker	emily johnson	t	\N	2024-08-27 10:00:00
Social Worker	emily johnson	f	1000033.0	2024-08-27 10:30:00
Social Worker	emily johnson	t	\N	2024-08-27 11:00:00
Social Worker	emily johnson	t	\N	2024-08-27 11:30:00
Social Worker	emily johnson	t	\N	2024-08-27 12:00:00
Social Worker	emily johnson	t	\N	2024-08-27 12:30:00
Social Worker	emily johnson	t	\N	2024-08-27 13:00:00
Social Worker	emily johnson	t	\N	2024-08-27 13:30:00
Social Worker	emily johnson	t	\N	2024-08-27 14:00:00
Social Worker	emily johnson	t	\N	2024-08-27 14:30:00
Social Worker	emily johnson	t	\N	2024-08-27 15:00:00
Social Worker	emily johnson	f	1000009.0	2024-08-27 15:30:00
Social Worker	emily johnson	t	\N	2024-08-27 16:00:00
Social Worker	emily johnson	t	\N	2024-08-27 16:30:00
Social Worker	emily johnson	f	1000010.0	2024-08-28 08:00:00
Social Worker	emily johnson	t	\N	2024-08-28 08:30:00
Social Worker	emily johnson	t	\N	2024-08-28 09:00:00
Social Worker	emily johnson	t	\N	2024-08-28 09:30:00
Social Worker	emily johnson	t	\N	2024-08-28 10:00:00
Social Worker	emily johnson	t	\N	2024-08-28 10:30:00
Social Worker	emily johnson	t	\N	2024-08-28 11:00:00
Social Worker	emily johnson	t	\N	2024-08-28 11:30:00
Social Worker	emily johnson	f	1000047.0	2024-08-28 12:00:00
Social Worker	emily johnson	f	1000064.0	2024-08-28 12:30:00
Social Worker	emily johnson	t	\N	2024-08-28 13:00:00
Social Worker	emily johnson	t	\N	2024-08-28 13:30:00
Social Worker	emily johnson	t	\N	2024-08-28 14:00:00
Social Worker	emily johnson	t	\N	2024-08-28 14:30:00
Social Worker	emily johnson	t	\N	2024-08-28 15:00:00
Social Worker	emily johnson	t	\N	2024-08-28 15:30:00
Social Worker	emily johnson	t	\N	2024-08-28 16:00:00
Social Worker	emily johnson	f	1000009.0	2024-08-28 16:30:00
Social Worker	emily johnson	f	1000100.0	2024-08-29 08:00:00
Social Worker	emily johnson	t	\N	2024-08-29 08:30:00
Social Worker	emily johnson	f	1000024.0	2024-08-29 09:00:00
Social Worker	emily johnson	t	\N	2024-08-29 09:30:00
Social Worker	emily johnson	t	\N	2024-08-29 10:00:00
Social Worker	emily johnson	f	1000010.0	2024-08-29 10:30:00
Social Worker	emily johnson	t	\N	2024-08-29 11:00:00
Social Worker	emily johnson	f	1000093.0	2024-08-29 11:30:00
Social Worker	emily johnson	t	\N	2024-08-29 12:00:00
Social Worker	emily johnson	t	\N	2024-08-29 12:30:00
Social Worker	emily johnson	f	1000073.0	2024-08-29 13:00:00
Social Worker	emily johnson	t	\N	2024-08-29 13:30:00
Social Worker	emily johnson	f	1000062.0	2024-08-29 14:00:00
Social Worker	emily johnson	t	\N	2024-08-29 14:30:00
Social Worker	emily johnson	t	\N	2024-08-29 15:00:00
Social Worker	emily johnson	f	1000023.0	2024-08-29 15:30:00
Social Worker	emily johnson	t	\N	2024-08-29 16:00:00
Social Worker	emily johnson	f	1000095.0	2024-08-29 16:30:00
Social Worker	emily johnson	t	\N	2024-08-30 08:00:00
Social Worker	emily johnson	t	\N	2024-08-30 08:30:00
Social Worker	emily johnson	t	\N	2024-08-30 09:00:00
Social Worker	emily johnson	f	1000053.0	2024-08-30 09:30:00
Social Worker	emily johnson	t	\N	2024-08-30 10:00:00
Social Worker	emily johnson	f	1000033.0	2024-08-30 10:30:00
Social Worker	emily johnson	t	\N	2024-08-30 11:00:00
Social Worker	emily johnson	f	1000095.0	2024-08-30 11:30:00
Social Worker	emily johnson	t	\N	2024-08-30 12:00:00
Social Worker	emily johnson	f	1000026.0	2024-08-30 12:30:00
Social Worker	emily johnson	t	\N	2024-08-30 13:00:00
Social Worker	emily johnson	f	1000068.0	2024-08-30 13:30:00
Social Worker	emily johnson	t	\N	2024-08-30 14:00:00
Social Worker	emily johnson	t	\N	2024-08-30 14:30:00
Social Worker	emily johnson	f	1000100.0	2024-08-30 15:00:00
Social Worker	emily johnson	f	1000039.0	2024-08-30 15:30:00
Social Worker	emily johnson	t	\N	2024-08-30 16:00:00
Social Worker	emily johnson	f	1000001.0	2024-08-30 16:30:00
Social Worker	emily johnson	t	\N	2024-08-31 09:00:00
Social Worker	emily johnson	t	\N	2024-08-31 09:30:00
Social Worker	emily johnson	t	\N	2024-08-31 10:00:00
Social Worker	emily johnson	t	\N	2024-08-31 10:30:00
Social Worker	emily johnson	t	\N	2024-08-31 11:00:00
Social Worker	emily johnson	t	\N	2024-08-31 11:30:00
Social Worker	emily johnson	t	\N	2024-08-31 12:00:00
Social Worker	emily johnson	t	\N	2024-08-31 12:30:00
Social Worker	emily johnson	f	1000036.0	2024-09-02 08:00:00
Social Worker	emily johnson	f	1000018.0	2024-09-02 08:30:00
Social Worker	emily johnson	t	\N	2024-09-02 09:00:00
Social Worker	emily johnson	t	\N	2024-09-02 09:30:00
Social Worker	emily johnson	f	1000019.0	2024-09-02 10:00:00
Social Worker	emily johnson	t	\N	2024-09-02 10:30:00
Social Worker	emily johnson	f	1000023.0	2024-09-02 11:00:00
Social Worker	emily johnson	t	\N	2024-09-02 11:30:00
Social Worker	emily johnson	t	\N	2024-09-02 12:00:00
Social Worker	emily johnson	t	\N	2024-09-02 12:30:00
Social Worker	emily johnson	t	\N	2024-09-02 13:00:00
Social Worker	emily johnson	t	\N	2024-09-02 13:30:00
Social Worker	emily johnson	f	1000016.0	2024-09-02 14:00:00
Social Worker	emily johnson	t	\N	2024-09-02 14:30:00
Social Worker	emily johnson	t	\N	2024-09-02 15:00:00
Social Worker	emily johnson	t	\N	2024-09-02 15:30:00
Social Worker	emily johnson	t	\N	2024-09-02 16:00:00
Social Worker	emily johnson	t	\N	2024-09-02 16:30:00
Social Worker	emily johnson	t	\N	2024-09-03 08:00:00
Social Worker	emily johnson	t	\N	2024-09-03 08:30:00
Social Worker	emily johnson	t	\N	2024-09-03 09:00:00
Social Worker	emily johnson	t	\N	2024-09-03 09:30:00
Social Worker	emily johnson	t	\N	2024-09-03 10:00:00
Social Worker	emily johnson	t	\N	2024-09-03 10:30:00
Social Worker	emily johnson	t	\N	2024-09-03 11:00:00
Social Worker	emily johnson	t	\N	2024-09-03 11:30:00
Social Worker	emily johnson	t	\N	2024-09-03 12:00:00
Social Worker	emily johnson	t	\N	2024-09-03 12:30:00
Social Worker	emily johnson	t	\N	2024-09-03 13:00:00
Social Worker	emily johnson	f	1000049.0	2024-09-03 13:30:00
Social Worker	emily johnson	t	\N	2024-09-03 14:00:00
Social Worker	emily johnson	t	\N	2024-09-03 14:30:00
Social Worker	emily johnson	f	1000042.0	2024-09-03 15:00:00
Social Worker	emily johnson	t	\N	2024-09-03 15:30:00
Social Worker	emily johnson	t	\N	2024-09-03 16:00:00
Social Worker	emily johnson	t	\N	2024-09-03 16:30:00
Nutritionist	jane smith	t	\N	2024-08-07 12:00:00
Nutritionist	jane smith	f	1000052.0	2024-08-07 12:30:00
Nutritionist	jane smith	t	\N	2024-08-07 13:00:00
Nutritionist	jane smith	t	\N	2024-08-07 13:30:00
Nutritionist	jane smith	t	\N	2024-08-07 14:00:00
Nutritionist	jane smith	t	\N	2024-08-07 14:30:00
Nutritionist	jane smith	t	\N	2024-08-07 15:00:00
Nutritionist	jane smith	t	\N	2024-08-07 15:30:00
Nutritionist	jane smith	t	\N	2024-08-07 16:00:00
Nutritionist	jane smith	t	\N	2024-08-07 16:30:00
Nutritionist	jane smith	f	10232303.0	2024-08-08 08:00:00
Nutritionist	jane smith	f	10232303.0	2024-08-08 08:30:00
Nutritionist	jane smith	f	10232303.0	2024-08-08 09:00:00
Nutritionist	jane smith	f	10232303.0	2024-08-08 09:30:00
Nutritionist	jane smith	t	\N	2024-08-08 10:00:00
Nutritionist	jane smith	f	1149973.0	2024-08-08 10:30:00
Nutritionist	jane smith	f	10232303.0	2024-08-08 11:00:00
Nutritionist	jane smith	f	1149973.0	2024-08-08 11:30:00
Nutritionist	jane smith	t	\N	2024-08-08 12:00:00
Nutritionist	jane smith	t	\N	2024-08-08 12:30:00
Nutritionist	jane smith	f	1000023.0	2024-08-08 13:00:00
Nutritionist	jane smith	t	\N	2024-08-08 13:30:00
Nutritionist	jane smith	t	\N	2024-08-08 14:00:00
Nutritionist	jane smith	f	1149973.0	2024-08-08 14:30:00
Nutritionist	jane smith	f	1000079.0	2024-08-08 15:00:00
Nutritionist	jane smith	t	\N	2024-08-08 15:30:00
Nutritionist	jane smith	f	1000004.0	2024-08-08 16:00:00
Nutritionist	jane smith	f	1000010.0	2024-08-08 16:30:00
Nutritionist	jane smith	t	\N	2024-08-09 08:00:00
Nutritionist	jane smith	t	\N	2024-08-09 08:30:00
Nutritionist	jane smith	t	\N	2024-08-09 09:00:00
Nutritionist	jane smith	f	1000052.0	2024-08-09 09:30:00
Nutritionist	jane smith	t	\N	2024-08-09 10:00:00
Nutritionist	jane smith	f	1000019.0	2024-08-09 10:30:00
Nutritionist	jane smith	f	1000058.0	2024-08-09 11:00:00
Nutritionist	jane smith	t	\N	2024-08-09 11:30:00
Nutritionist	jane smith	t	\N	2024-08-09 12:00:00
Nutritionist	jane smith	f	1000081.0	2024-08-09 12:30:00
Nutritionist	jane smith	t	\N	2024-08-09 13:00:00
Nutritionist	jane smith	t	\N	2024-08-09 13:30:00
Nutritionist	jane smith	t	\N	2024-08-09 14:00:00
Nutritionist	jane smith	t	\N	2024-08-09 14:30:00
Nutritionist	jane smith	t	\N	2024-08-09 15:00:00
Nutritionist	jane smith	f	1000082.0	2024-08-09 15:30:00
Nutritionist	jane smith	f	1000073.0	2024-08-09 16:00:00
Nutritionist	jane smith	f	1000043.0	2024-08-09 16:30:00
Nutritionist	jane smith	f	1000004.0	2024-08-10 09:00:00
Nutritionist	jane smith	t	\N	2024-08-10 09:30:00
Nutritionist	jane smith	t	\N	2024-08-10 10:00:00
Nutritionist	jane smith	t	\N	2024-08-10 10:30:00
Nutritionist	jane smith	t	\N	2024-08-10 11:00:00
Nutritionist	jane smith	t	\N	2024-08-10 11:30:00
Nutritionist	jane smith	t	\N	2024-08-10 12:00:00
Nutritionist	jane smith	t	\N	2024-08-10 12:30:00
Nutritionist	jane smith	t	\N	2024-08-12 08:00:00
Nutritionist	jane smith	t	\N	2024-08-12 08:30:00
Nutritionist	jane smith	t	\N	2024-08-12 09:00:00
Nutritionist	jane smith	t	\N	2024-08-12 09:30:00
Nutritionist	jane smith	f	1000010.0	2024-08-12 10:00:00
Nutritionist	jane smith	t	\N	2024-08-12 10:30:00
Nutritionist	jane smith	t	\N	2024-08-12 11:00:00
Nutritionist	jane smith	f	1000046.0	2024-08-12 11:30:00
Nutritionist	jane smith	f	1000012.0	2024-08-12 12:00:00
Nutritionist	jane smith	t	\N	2024-08-12 12:30:00
Nutritionist	jane smith	t	\N	2024-08-12 13:00:00
Nutritionist	jane smith	f	1000068.0	2024-08-12 13:30:00
Nutritionist	jane smith	t	\N	2024-08-12 14:00:00
Nutritionist	jane smith	t	\N	2024-08-12 14:30:00
Nutritionist	jane smith	t	\N	2024-08-12 15:00:00
Nutritionist	jane smith	t	\N	2024-08-12 15:30:00
Nutritionist	jane smith	t	\N	2024-08-12 16:00:00
Nutritionist	jane smith	t	\N	2024-08-12 16:30:00
Nutritionist	jane smith	t	\N	2024-08-13 08:00:00
Nutritionist	jane smith	t	\N	2024-08-13 08:30:00
Nutritionist	jane smith	t	\N	2024-08-13 09:00:00
Nutritionist	jane smith	f	1000049.0	2024-08-13 09:30:00
Nutritionist	jane smith	t	\N	2024-08-13 10:00:00
Nutritionist	jane smith	t	\N	2024-08-13 10:30:00
Nutritionist	jane smith	t	\N	2024-08-13 11:00:00
Nutritionist	jane smith	t	\N	2024-08-13 11:30:00
Nutritionist	jane smith	t	\N	2024-08-13 12:00:00
Nutritionist	jane smith	t	\N	2024-08-13 12:30:00
Nutritionist	jane smith	t	\N	2024-08-13 13:00:00
Nutritionist	jane smith	f	1000023.0	2024-08-13 13:30:00
Nutritionist	jane smith	t	\N	2024-08-13 14:00:00
Nutritionist	jane smith	t	\N	2024-08-13 14:30:00
Nutritionist	jane smith	t	\N	2024-08-13 15:00:00
Nutritionist	jane smith	t	\N	2024-08-13 15:30:00
Nutritionist	jane smith	t	\N	2024-08-13 16:00:00
Nutritionist	jane smith	t	\N	2024-08-13 16:30:00
Nutritionist	jane smith	f	1000098.0	2024-08-14 08:00:00
Nutritionist	jane smith	t	\N	2024-08-14 08:30:00
Nutritionist	jane smith	t	\N	2024-08-14 09:00:00
Nutritionist	jane smith	t	\N	2024-08-14 09:30:00
Nutritionist	jane smith	t	\N	2024-08-14 10:00:00
Nutritionist	jane smith	t	\N	2024-08-14 10:30:00
Nutritionist	jane smith	t	\N	2024-08-14 11:00:00
Nutritionist	jane smith	t	\N	2024-08-14 11:30:00
Nutritionist	jane smith	f	1000090.0	2024-08-14 12:00:00
Nutritionist	jane smith	t	\N	2024-08-14 12:30:00
Nutritionist	jane smith	f	1000083.0	2024-08-14 13:00:00
Nutritionist	jane smith	t	\N	2024-08-14 13:30:00
Nutritionist	jane smith	f	1000062.0	2024-08-14 14:00:00
Nutritionist	jane smith	t	\N	2024-08-14 14:30:00
Nutritionist	jane smith	t	\N	2024-08-14 15:00:00
Nutritionist	jane smith	f	1000061.0	2024-08-14 15:30:00
Nutritionist	jane smith	f	1000048.0	2024-08-14 16:00:00
Nutritionist	jane smith	t	\N	2024-08-14 16:30:00
Nutritionist	jane smith	t	\N	2024-08-15 08:00:00
Nutritionist	jane smith	t	\N	2024-08-15 08:30:00
Nutritionist	jane smith	t	\N	2024-08-15 09:00:00
Nutritionist	jane smith	t	\N	2024-08-15 09:30:00
Nutritionist	jane smith	t	\N	2024-08-15 10:00:00
Nutritionist	jane smith	f	1000087.0	2024-08-15 10:30:00
Nutritionist	jane smith	f	1000083.0	2024-08-15 11:00:00
Nutritionist	jane smith	f	1000057.0	2024-08-15 11:30:00
Nutritionist	jane smith	t	\N	2024-08-15 12:00:00
Nutritionist	jane smith	t	\N	2024-08-15 12:30:00
Nutritionist	jane smith	f	1000050.0	2024-08-15 13:00:00
Nutritionist	jane smith	t	\N	2024-08-15 13:30:00
Nutritionist	jane smith	t	\N	2024-08-15 14:00:00
Nutritionist	jane smith	t	\N	2024-08-15 14:30:00
Nutritionist	jane smith	f	1000052.0	2024-08-15 15:00:00
Nutritionist	jane smith	t	\N	2024-08-15 15:30:00
Nutritionist	jane smith	f	1000079.0	2024-08-15 16:00:00
Nutritionist	jane smith	t	\N	2024-08-15 16:30:00
Nutritionist	jane smith	t	\N	2024-08-16 08:00:00
Nutritionist	jane smith	t	\N	2024-08-16 08:30:00
Nutritionist	jane smith	t	\N	2024-08-16 09:00:00
Nutritionist	jane smith	t	\N	2024-08-16 09:30:00
Nutritionist	jane smith	t	\N	2024-08-16 10:00:00
Nutritionist	jane smith	t	\N	2024-08-16 10:30:00
Nutritionist	jane smith	f	1000081.0	2024-08-16 11:00:00
Nutritionist	jane smith	t	\N	2024-08-16 11:30:00
Nutritionist	jane smith	t	\N	2024-08-16 12:00:00
Nutritionist	jane smith	f	1000029.0	2024-08-16 12:30:00
Nutritionist	jane smith	t	\N	2024-08-16 13:00:00
Nutritionist	jane smith	f	1000010.0	2024-08-16 13:30:00
Nutritionist	jane smith	t	\N	2024-08-16 14:00:00
Nutritionist	jane smith	t	\N	2024-08-16 14:30:00
Nutritionist	jane smith	f	1000040.0	2024-08-16 15:00:00
Nutritionist	jane smith	t	\N	2024-08-16 15:30:00
Nutritionist	jane smith	f	1000041.0	2024-08-16 16:00:00
Nutritionist	jane smith	f	1000039.0	2024-08-16 16:30:00
Nutritionist	jane smith	t	\N	2024-08-17 09:00:00
Nutritionist	jane smith	t	\N	2024-08-17 09:30:00
Nutritionist	jane smith	t	\N	2024-08-17 10:00:00
Nutritionist	jane smith	f	1000074.0	2024-08-17 10:30:00
Nutritionist	jane smith	f	1000015.0	2024-08-17 11:00:00
Nutritionist	jane smith	t	\N	2024-08-17 11:30:00
Nutritionist	jane smith	t	\N	2024-08-17 12:00:00
Nutritionist	jane smith	t	\N	2024-08-17 12:30:00
Nutritionist	jane smith	t	\N	2024-08-19 08:00:00
Nutritionist	jane smith	t	\N	2024-08-19 08:30:00
Nutritionist	jane smith	t	\N	2024-08-19 09:00:00
Nutritionist	jane smith	t	\N	2024-08-19 09:30:00
Nutritionist	jane smith	f	1000083.0	2024-08-19 10:00:00
Nutritionist	jane smith	t	\N	2024-08-19 10:30:00
Nutritionist	jane smith	t	\N	2024-08-19 11:00:00
Nutritionist	jane smith	t	\N	2024-08-19 11:30:00
Nutritionist	jane smith	t	\N	2024-08-19 12:00:00
Nutritionist	jane smith	t	\N	2024-08-19 12:30:00
Nutritionist	jane smith	t	\N	2024-08-19 13:00:00
Nutritionist	jane smith	f	1000091.0	2024-08-19 13:30:00
Nutritionist	jane smith	t	\N	2024-08-19 14:00:00
Nutritionist	jane smith	t	\N	2024-08-19 14:30:00
Nutritionist	jane smith	t	\N	2024-08-19 15:00:00
Nutritionist	jane smith	t	\N	2024-08-19 15:30:00
Nutritionist	jane smith	t	\N	2024-08-19 16:00:00
Nutritionist	jane smith	t	\N	2024-08-19 16:30:00
Nutritionist	jane smith	t	\N	2024-08-20 08:00:00
Nutritionist	jane smith	f	1000026.0	2024-08-20 08:30:00
Nutritionist	jane smith	f	1000075.0	2024-08-20 09:00:00
Nutritionist	jane smith	f	1000067.0	2024-08-20 09:30:00
Nutritionist	jane smith	f	1000027.0	2024-08-20 10:00:00
Nutritionist	jane smith	t	\N	2024-08-20 10:30:00
Nutritionist	jane smith	f	1000076.0	2024-08-20 11:00:00
Nutritionist	jane smith	f	1000058.0	2024-08-20 11:30:00
Nutritionist	jane smith	f	1000064.0	2024-08-20 12:00:00
Nutritionist	jane smith	t	\N	2024-08-20 12:30:00
Nutritionist	jane smith	f	1000060.0	2024-08-20 13:00:00
Nutritionist	jane smith	f	1000068.0	2024-08-20 13:30:00
Nutritionist	jane smith	t	\N	2024-08-20 14:00:00
Nutritionist	jane smith	t	\N	2024-08-20 14:30:00
Nutritionist	jane smith	t	\N	2024-08-20 15:00:00
Nutritionist	jane smith	f	1000017.0	2024-08-20 15:30:00
Nutritionist	jane smith	f	1000025.0	2024-08-20 16:00:00
Nutritionist	jane smith	t	\N	2024-08-20 16:30:00
Nutritionist	jane smith	t	\N	2024-08-21 08:00:00
Nutritionist	jane smith	t	\N	2024-08-21 08:30:00
Nutritionist	jane smith	f	1000060.0	2024-08-21 09:00:00
Nutritionist	jane smith	t	\N	2024-08-21 09:30:00
Nutritionist	jane smith	t	\N	2024-08-21 10:00:00
Nutritionist	jane smith	f	1000090.0	2024-08-21 10:30:00
Nutritionist	jane smith	t	\N	2024-08-21 11:00:00
Nutritionist	jane smith	f	1000001.0	2024-08-21 11:30:00
Nutritionist	jane smith	t	\N	2024-08-21 12:00:00
Nutritionist	jane smith	t	\N	2024-08-21 12:30:00
Nutritionist	jane smith	t	\N	2024-08-21 13:00:00
Nutritionist	jane smith	f	1000053.0	2024-08-21 13:30:00
Nutritionist	jane smith	t	\N	2024-08-21 14:00:00
Nutritionist	jane smith	f	1000064.0	2024-08-21 14:30:00
Nutritionist	jane smith	t	\N	2024-08-21 15:00:00
Nutritionist	jane smith	f	1000039.0	2024-08-21 15:30:00
Nutritionist	jane smith	t	\N	2024-08-21 16:00:00
Nutritionist	jane smith	f	1000077.0	2024-08-21 16:30:00
Nutritionist	jane smith	t	\N	2024-08-22 08:00:00
Nutritionist	jane smith	t	\N	2024-08-22 08:30:00
Nutritionist	jane smith	f	1000030.0	2024-08-22 09:00:00
Nutritionist	jane smith	f	1000098.0	2024-08-22 09:30:00
Nutritionist	jane smith	t	\N	2024-08-22 10:00:00
Nutritionist	jane smith	f	1000037.0	2024-08-22 10:30:00
Nutritionist	jane smith	t	\N	2024-08-22 11:00:00
Nutritionist	jane smith	t	\N	2024-08-22 11:30:00
Nutritionist	jane smith	f	1000096.0	2024-08-22 12:00:00
Nutritionist	jane smith	f	1000063.0	2024-08-22 12:30:00
Nutritionist	jane smith	t	\N	2024-08-22 13:00:00
Nutritionist	jane smith	t	\N	2024-08-22 13:30:00
Nutritionist	jane smith	t	\N	2024-08-22 14:00:00
Nutritionist	jane smith	f	1000035.0	2024-08-22 14:30:00
Nutritionist	jane smith	t	\N	2024-08-22 15:00:00
Nutritionist	jane smith	t	\N	2024-08-22 15:30:00
Nutritionist	jane smith	t	\N	2024-08-22 16:00:00
Nutritionist	jane smith	f	1000058.0	2024-08-22 16:30:00
Nutritionist	jane smith	t	\N	2024-08-23 08:00:00
Nutritionist	jane smith	t	\N	2024-08-23 08:30:00
Nutritionist	jane smith	t	\N	2024-08-23 09:00:00
Nutritionist	jane smith	t	\N	2024-08-23 09:30:00
Nutritionist	jane smith	t	\N	2024-08-23 10:00:00
Nutritionist	jane smith	t	\N	2024-08-23 10:30:00
Nutritionist	jane smith	t	\N	2024-08-23 11:00:00
Nutritionist	jane smith	t	\N	2024-08-23 11:30:00
Nutritionist	jane smith	t	\N	2024-08-23 12:00:00
Nutritionist	jane smith	t	\N	2024-08-23 12:30:00
Nutritionist	jane smith	t	\N	2024-08-23 13:00:00
Nutritionist	jane smith	t	\N	2024-08-23 13:30:00
Nutritionist	jane smith	t	\N	2024-08-23 14:00:00
Nutritionist	jane smith	f	1000021.0	2024-08-23 14:30:00
Nutritionist	jane smith	f	1000073.0	2024-08-23 15:00:00
Nutritionist	jane smith	t	\N	2024-08-23 15:30:00
Nutritionist	jane smith	f	1000023.0	2024-08-23 16:00:00
Nutritionist	jane smith	t	\N	2024-08-23 16:30:00
Nutritionist	jane smith	t	\N	2024-08-24 09:00:00
Nutritionist	jane smith	t	\N	2024-08-24 09:30:00
Nutritionist	jane smith	f	1000051.0	2024-08-24 10:00:00
Nutritionist	jane smith	t	\N	2024-08-24 10:30:00
Nutritionist	jane smith	t	\N	2024-08-24 11:00:00
Nutritionist	jane smith	f	1000023.0	2024-08-24 11:30:00
Nutritionist	jane smith	t	\N	2024-08-24 12:00:00
Nutritionist	jane smith	t	\N	2024-08-24 12:30:00
Nutritionist	jane smith	f	1000091.0	2024-08-26 08:00:00
Nutritionist	jane smith	f	1000019.0	2024-08-26 08:30:00
Nutritionist	jane smith	t	\N	2024-08-26 09:00:00
Nutritionist	jane smith	f	1000075.0	2024-08-26 09:30:00
Nutritionist	jane smith	f	1000033.0	2024-08-26 10:00:00
Nutritionist	jane smith	f	1000021.0	2024-08-26 10:30:00
Nutritionist	jane smith	f	1000013.0	2024-08-26 11:00:00
Nutritionist	jane smith	f	1000074.0	2024-08-26 11:30:00
Nutritionist	jane smith	t	\N	2024-08-26 12:00:00
Nutritionist	jane smith	t	\N	2024-08-26 12:30:00
Nutritionist	jane smith	t	\N	2024-08-26 13:00:00
Nutritionist	jane smith	f	1000072.0	2024-08-26 13:30:00
Nutritionist	jane smith	t	\N	2024-08-26 14:00:00
Nutritionist	jane smith	f	1000073.0	2024-08-26 14:30:00
Nutritionist	jane smith	t	\N	2024-08-26 15:00:00
Nutritionist	jane smith	t	\N	2024-08-26 15:30:00
Nutritionist	jane smith	t	\N	2024-08-26 16:00:00
Nutritionist	jane smith	t	\N	2024-08-26 16:30:00
Nutritionist	jane smith	t	\N	2024-08-27 08:00:00
Nutritionist	jane smith	t	\N	2024-08-27 08:30:00
Nutritionist	jane smith	t	\N	2024-08-27 09:00:00
Nutritionist	jane smith	t	\N	2024-08-27 09:30:00
Nutritionist	jane smith	t	\N	2024-08-27 10:00:00
Nutritionist	jane smith	f	1000062.0	2024-08-27 10:30:00
Nutritionist	jane smith	f	1000004.0	2024-08-27 11:00:00
Nutritionist	jane smith	t	\N	2024-08-27 11:30:00
Nutritionist	jane smith	t	\N	2024-08-27 12:00:00
Nutritionist	jane smith	t	\N	2024-08-27 12:30:00
Nutritionist	jane smith	t	\N	2024-08-27 13:00:00
Nutritionist	jane smith	t	\N	2024-08-27 13:30:00
Nutritionist	jane smith	f	1000006.0	2024-08-27 14:00:00
Nutritionist	jane smith	t	\N	2024-08-27 14:30:00
Nutritionist	jane smith	t	\N	2024-08-27 15:00:00
Nutritionist	jane smith	t	\N	2024-08-27 15:30:00
Nutritionist	jane smith	t	\N	2024-08-27 16:00:00
Nutritionist	jane smith	t	\N	2024-08-27 16:30:00
Nutritionist	jane smith	t	\N	2024-08-28 08:00:00
Nutritionist	jane smith	t	\N	2024-08-28 08:30:00
Nutritionist	jane smith	t	\N	2024-08-28 09:00:00
Nutritionist	jane smith	f	1000072.0	2024-08-28 09:30:00
Nutritionist	jane smith	t	\N	2024-08-28 10:00:00
Nutritionist	jane smith	t	\N	2024-08-28 10:30:00
Nutritionist	jane smith	f	1000077.0	2024-08-28 11:00:00
Nutritionist	jane smith	t	\N	2024-08-28 11:30:00
Nutritionist	jane smith	t	\N	2024-08-28 12:00:00
Nutritionist	jane smith	t	\N	2024-08-28 12:30:00
Nutritionist	jane smith	t	\N	2024-08-28 13:00:00
Nutritionist	jane smith	t	\N	2024-08-28 13:30:00
Nutritionist	jane smith	f	1000002.0	2024-08-28 14:00:00
Nutritionist	jane smith	f	1000041.0	2024-08-28 14:30:00
Nutritionist	jane smith	t	\N	2024-08-28 15:00:00
Nutritionist	jane smith	f	1000047.0	2024-08-28 15:30:00
Nutritionist	jane smith	t	\N	2024-08-28 16:00:00
Nutritionist	jane smith	t	\N	2024-08-28 16:30:00
Nutritionist	jane smith	t	\N	2024-08-29 08:00:00
Nutritionist	jane smith	f	1000091.0	2024-08-29 08:30:00
Nutritionist	jane smith	t	\N	2024-08-29 09:00:00
Nutritionist	jane smith	t	\N	2024-08-29 09:30:00
Nutritionist	jane smith	t	\N	2024-08-29 10:00:00
Nutritionist	jane smith	t	\N	2024-08-29 10:30:00
Nutritionist	jane smith	t	\N	2024-08-29 11:00:00
Nutritionist	jane smith	f	1000055.0	2024-08-29 11:30:00
Nutritionist	jane smith	t	\N	2024-08-29 12:00:00
Nutritionist	jane smith	t	\N	2024-08-29 12:30:00
Nutritionist	jane smith	f	1000043.0	2024-08-29 13:00:00
Nutritionist	jane smith	t	\N	2024-08-29 13:30:00
Nutritionist	jane smith	f	1000003.0	2024-08-29 14:00:00
Nutritionist	jane smith	t	\N	2024-08-29 14:30:00
Nutritionist	jane smith	t	\N	2024-08-29 15:00:00
Nutritionist	jane smith	t	\N	2024-08-29 15:30:00
Nutritionist	jane smith	f	1000015.0	2024-08-29 16:00:00
Nutritionist	jane smith	f	1000009.0	2024-08-29 16:30:00
Nutritionist	jane smith	f	1000025.0	2024-08-30 08:00:00
Nutritionist	jane smith	t	\N	2024-08-30 08:30:00
Nutritionist	jane smith	f	1000018.0	2024-08-30 09:00:00
Nutritionist	jane smith	t	\N	2024-08-30 09:30:00
Nutritionist	jane smith	t	\N	2024-08-30 10:00:00
Nutritionist	jane smith	t	\N	2024-08-30 10:30:00
Nutritionist	jane smith	f	1000060.0	2024-08-30 11:00:00
Nutritionist	jane smith	t	\N	2024-08-30 11:30:00
Nutritionist	jane smith	t	\N	2024-08-30 12:00:00
Nutritionist	jane smith	f	1000065.0	2024-08-30 12:30:00
Nutritionist	jane smith	t	\N	2024-08-30 13:00:00
Nutritionist	jane smith	t	\N	2024-08-30 13:30:00
Nutritionist	jane smith	t	\N	2024-08-30 14:00:00
Nutritionist	jane smith	t	\N	2024-08-30 14:30:00
Nutritionist	jane smith	t	\N	2024-08-30 15:00:00
Nutritionist	jane smith	t	\N	2024-08-30 15:30:00
Nutritionist	jane smith	t	\N	2024-08-30 16:00:00
Nutritionist	jane smith	f	1000061.0	2024-08-30 16:30:00
Nutritionist	jane smith	t	\N	2024-08-31 09:00:00
Nutritionist	jane smith	t	\N	2024-08-31 09:30:00
Nutritionist	jane smith	f	1000089.0	2024-08-31 10:00:00
Nutritionist	jane smith	t	\N	2024-08-31 10:30:00
Nutritionist	jane smith	t	\N	2024-08-31 11:00:00
Nutritionist	jane smith	t	\N	2024-08-31 11:30:00
Nutritionist	jane smith	t	\N	2024-08-31 12:00:00
Nutritionist	jane smith	f	1000093.0	2024-08-31 12:30:00
Nutritionist	jane smith	t	\N	2024-09-02 08:00:00
Nutritionist	jane smith	t	\N	2024-09-02 08:30:00
Nutritionist	jane smith	t	\N	2024-09-02 09:00:00
Nutritionist	jane smith	t	\N	2024-09-02 09:30:00
Nutritionist	jane smith	t	\N	2024-09-02 10:00:00
Nutritionist	jane smith	t	\N	2024-09-02 10:30:00
Nutritionist	jane smith	t	\N	2024-09-02 11:00:00
Nutritionist	jane smith	f	1000086.0	2024-09-02 11:30:00
Nutritionist	jane smith	t	\N	2024-09-02 12:00:00
Nutritionist	jane smith	f	1000024.0	2024-09-02 12:30:00
Nutritionist	jane smith	t	\N	2024-09-02 13:00:00
Nutritionist	jane smith	f	1000020.0	2024-09-02 13:30:00
Nutritionist	jane smith	t	\N	2024-09-02 14:00:00
Nutritionist	jane smith	f	1000003.0	2024-09-02 14:30:00
Nutritionist	jane smith	t	\N	2024-09-02 15:00:00
Nutritionist	jane smith	f	1000056.0	2024-09-02 15:30:00
Nutritionist	jane smith	t	\N	2024-09-02 16:00:00
Nutritionist	jane smith	t	\N	2024-09-02 16:30:00
Nutritionist	jane smith	t	\N	2024-09-03 08:00:00
Nutritionist	jane smith	t	\N	2024-09-03 08:30:00
Nutritionist	jane smith	t	\N	2024-09-03 09:00:00
Nutritionist	jane smith	t	\N	2024-09-03 09:30:00
Nutritionist	jane smith	t	\N	2024-09-03 10:00:00
Nutritionist	jane smith	t	\N	2024-09-03 10:30:00
Nutritionist	jane smith	t	\N	2024-09-03 11:00:00
Nutritionist	jane smith	t	\N	2024-09-03 11:30:00
Nutritionist	jane smith	t	\N	2024-09-03 12:00:00
Nutritionist	jane smith	t	\N	2024-09-03 12:30:00
Nutritionist	jane smith	t	\N	2024-09-03 13:00:00
Nutritionist	jane smith	f	1000069.0	2024-09-03 13:30:00
Nutritionist	jane smith	t	\N	2024-09-03 14:00:00
Nutritionist	jane smith	t	\N	2024-09-03 14:30:00
Nutritionist	jane smith	t	\N	2024-09-03 15:00:00
Nutritionist	jane smith	t	\N	2024-09-03 15:30:00
Nutritionist	jane smith	t	\N	2024-09-03 16:00:00
Nutritionist	jane smith	t	\N	2024-09-03 16:30:00
Pharmacist	michael green	f	1000070.0	2024-08-26 08:30:00
Pharmacist	michael green	t	\N	2024-08-26 09:00:00
Pharmacist	michael green	f	1000056.0	2024-08-26 09:30:00
Pharmacist	michael green	t	\N	2024-08-26 10:00:00
Pharmacist	michael green	t	\N	2024-08-26 10:30:00
Pharmacist	michael green	t	\N	2024-08-26 11:00:00
Pharmacist	michael green	t	\N	2024-08-26 11:30:00
Pharmacist	michael green	t	\N	2024-08-26 12:00:00
Pharmacist	michael green	t	\N	2024-08-26 12:30:00
Pharmacist	michael green	f	1000066.0	2024-08-26 13:00:00
Pharmacist	michael green	f	1000080.0	2024-08-26 13:30:00
Pharmacist	michael green	f	1000067.0	2024-08-26 14:00:00
Pharmacist	michael green	t	\N	2024-08-26 14:30:00
Pharmacist	michael green	t	\N	2024-08-26 15:00:00
Pharmacist	michael green	t	\N	2024-08-26 15:30:00
Pharmacist	michael green	f	1000074.0	2024-08-26 16:00:00
Pharmacist	michael green	t	\N	2024-08-26 16:30:00
Pharmacist	michael green	t	\N	2024-08-27 08:00:00
Pharmacist	michael green	f	1000050.0	2024-08-27 08:30:00
Pharmacist	michael green	f	1000093.0	2024-08-27 09:00:00
Pharmacist	michael green	f	1000032.0	2024-08-27 09:30:00
Pharmacist	michael green	f	1000072.0	2024-08-27 10:00:00
Pharmacist	michael green	t	\N	2024-08-27 10:30:00
Pharmacist	michael green	t	\N	2024-08-27 11:00:00
Pharmacist	michael green	t	\N	2024-08-27 11:30:00
Pharmacist	michael green	t	\N	2024-08-27 12:00:00
Pharmacist	michael green	t	\N	2024-08-27 12:30:00
Pharmacist	michael green	t	\N	2024-08-27 13:00:00
Pharmacist	michael green	t	\N	2024-08-27 13:30:00
Pharmacist	michael green	t	\N	2024-08-27 14:00:00
Pharmacist	michael green	f	1000034.0	2024-08-27 14:30:00
Pharmacist	michael green	t	\N	2024-08-27 15:00:00
Pharmacist	michael green	t	\N	2024-08-27 15:30:00
Pharmacist	michael green	f	1000041.0	2024-08-27 16:00:00
Pharmacist	michael green	t	\N	2024-08-27 16:30:00
Pharmacist	michael green	t	\N	2024-08-28 08:00:00
Pharmacist	michael green	t	\N	2024-08-28 08:30:00
Pharmacist	michael green	t	\N	2024-08-28 09:00:00
Pharmacist	michael green	f	1000021.0	2024-08-28 09:30:00
Pharmacist	michael green	f	1000064.0	2024-08-28 10:00:00
Pharmacist	michael green	t	\N	2024-08-28 10:30:00
Pharmacist	michael green	t	\N	2024-08-28 11:00:00
Pharmacist	michael green	t	\N	2024-08-28 11:30:00
Pharmacist	michael green	t	\N	2024-08-28 12:00:00
Pharmacist	michael green	t	\N	2024-08-28 12:30:00
Pharmacist	michael green	t	\N	2024-08-28 13:00:00
Pharmacist	michael green	t	\N	2024-08-28 13:30:00
Pharmacist	michael green	t	\N	2024-08-28 14:00:00
Pharmacist	michael green	f	1000090.0	2024-08-28 14:30:00
Pharmacist	michael green	t	\N	2024-08-28 15:00:00
Pharmacist	michael green	t	\N	2024-08-28 15:30:00
Pharmacist	michael green	t	\N	2024-08-28 16:00:00
Pharmacist	michael green	t	\N	2024-08-28 16:30:00
Pharmacist	michael green	t	\N	2024-08-29 08:00:00
Pharmacist	michael green	f	1000058.0	2024-08-29 08:30:00
Pharmacist	michael green	f	1000062.0	2024-08-29 09:00:00
Pharmacist	michael green	t	\N	2024-08-29 09:30:00
Pharmacist	michael green	f	1000100.0	2024-08-29 10:00:00
Pharmacist	michael green	f	1000017.0	2024-08-29 10:30:00
Pharmacist	michael green	t	\N	2024-08-29 11:00:00
Pharmacist	michael green	f	1000092.0	2024-08-29 11:30:00
Pharmacist	michael green	t	\N	2024-08-29 12:00:00
Pharmacist	michael green	t	\N	2024-08-29 12:30:00
Pharmacist	michael green	t	\N	2024-08-29 13:00:00
Pharmacist	michael green	t	\N	2024-08-29 13:30:00
Pharmacist	michael green	t	\N	2024-08-29 14:00:00
Pharmacist	michael green	t	\N	2024-08-29 14:30:00
Pharmacist	michael green	t	\N	2024-08-29 15:00:00
Pharmacist	michael green	t	\N	2024-08-29 15:30:00
Pharmacist	michael green	t	\N	2024-08-29 16:00:00
Pharmacist	michael green	t	\N	2024-08-29 16:30:00
Pharmacist	michael green	t	\N	2024-08-30 08:00:00
Pharmacist	michael green	f	1000005.0	2024-08-30 08:30:00
Pharmacist	michael green	f	1000065.0	2024-08-30 09:00:00
Pharmacist	michael green	f	1000028.0	2024-08-30 09:30:00
Pharmacist	michael green	f	1000019.0	2024-08-30 10:00:00
Pharmacist	michael green	f	1000027.0	2024-08-30 10:30:00
Pharmacist	michael green	t	\N	2024-08-30 11:00:00
Pharmacist	michael green	t	\N	2024-08-30 11:30:00
Pharmacist	michael green	t	\N	2024-08-30 12:00:00
Pharmacist	michael green	t	\N	2024-08-30 12:30:00
Pharmacist	michael green	t	\N	2024-08-30 13:00:00
Pharmacist	michael green	f	1000079.0	2024-08-30 13:30:00
Pharmacist	michael green	t	\N	2024-08-30 14:00:00
Registered Nurse	susan davis	f	1000027.0	2024-08-05 08:00:00
Registered Nurse	susan davis	f	1000089.0	2024-08-05 08:30:00
Registered Nurse	susan davis	f	1000068.0	2024-08-05 09:00:00
Registered Nurse	susan davis	f	1000039.0	2024-08-05 09:30:00
Registered Nurse	susan davis	f	1000014.0	2024-08-05 10:00:00
Registered Nurse	susan davis	f	1000052.0	2024-08-05 10:30:00
Registered Nurse	susan davis	f	1000014.0	2024-08-05 11:00:00
Registered Nurse	susan davis	f	1000084.0	2024-08-05 11:30:00
Registered Nurse	susan davis	f	1000055.0	2024-08-05 12:00:00
Registered Nurse	susan davis	f	1000056.0	2024-08-05 12:30:00
Registered Nurse	susan davis	f	1000078.0	2024-08-05 13:00:00
Registered Nurse	susan davis	f	1000041.0	2024-08-05 13:30:00
Registered Nurse	susan davis	f	1000040.0	2024-08-05 14:00:00
Pharmacist	michael green	t	\N	2024-08-30 14:30:00
Registered Nurse	susan davis	f	1000034.0	2024-08-05 14:30:00
Registered Nurse	susan davis	f	1000048.0	2024-08-05 15:00:00
Registered Nurse	susan davis	f	1000000.0	2024-08-05 15:30:00
Registered Nurse	susan davis	f	1000086.0	2024-08-05 16:00:00
Registered Nurse	susan davis	f	1000029.0	2024-08-05 16:30:00
Registered Nurse	susan davis	f	1000012.0	2024-08-06 08:00:00
Registered Nurse	susan davis	f	1000004.0	2024-08-06 08:30:00
Registered Nurse	susan davis	f	1000047.0	2024-08-06 09:00:00
Registered Nurse	susan davis	f	1000008.0	2024-08-06 09:30:00
Registered Nurse	susan davis	f	1000052.0	2024-08-06 10:00:00
Registered Nurse	susan davis	f	1000019.0	2024-08-06 10:30:00
Registered Nurse	susan davis	f	1000023.0	2024-08-06 11:00:00
Registered Nurse	susan davis	f	1000081.0	2024-08-06 11:30:00
Registered Nurse	susan davis	f	1000070.0	2024-08-06 12:00:00
Registered Nurse	susan davis	f	1000081.0	2024-08-06 12:30:00
Registered Nurse	susan davis	f	1000048.0	2024-08-06 13:00:00
Registered Nurse	susan davis	f	1000033.0	2024-08-06 13:30:00
Registered Nurse	susan davis	f	1000057.0	2024-08-06 14:00:00
Registered Nurse	susan davis	f	1000032.0	2024-08-06 14:30:00
Registered Nurse	susan davis	f	1000002.0	2024-08-06 15:00:00
Registered Nurse	susan davis	f	1000007.0	2024-08-06 15:30:00
Registered Nurse	susan davis	f	1000069.0	2024-08-06 16:00:00
Registered Nurse	susan davis	f	1000023.0	2024-08-06 16:30:00
Registered Nurse	susan davis	t	\N	2024-08-07 08:00:00
Registered Nurse	susan davis	f	1000011.0	2024-08-07 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-07 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-07 09:30:00
Registered Nurse	susan davis	f	1000065.0	2024-08-07 10:00:00
Registered Nurse	susan davis	f	1000015.0	2024-08-07 10:30:00
Registered Nurse	susan davis	f	1000082.0	2024-08-07 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-07 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-07 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-07 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-07 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-07 13:30:00
Registered Nurse	susan davis	t	\N	2024-08-07 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-07 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-07 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-07 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-07 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-07 16:30:00
Registered Nurse	susan davis	f	1000051.0	2024-08-08 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-08 08:30:00
Registered Nurse	susan davis	f	1000003.0	2024-08-08 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-08 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-08 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-08 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-08 11:00:00
Registered Nurse	susan davis	f	1000010.0	2024-08-08 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-08 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-08 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-08 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-08 13:30:00
Registered Nurse	susan davis	t	\N	2024-08-08 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-08 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-08 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-08 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-08 16:00:00
Registered Nurse	susan davis	f	1000095.0	2024-08-08 16:30:00
Registered Nurse	susan davis	f	1000098.0	2024-08-09 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-09 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-09 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-09 09:30:00
Registered Nurse	susan davis	f	1000055.0	2024-08-09 10:00:00
Registered Nurse	susan davis	f	1000029.0	2024-08-09 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-09 11:00:00
Registered Nurse	susan davis	f	1000033.0	2024-08-09 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-09 12:00:00
Registered Nurse	susan davis	f	1000096.0	2024-08-09 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-09 13:00:00
Registered Nurse	susan davis	f	1000008.0	2024-08-09 13:30:00
Registered Nurse	susan davis	f	1000021.0	2024-08-09 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-09 14:30:00
Registered Nurse	susan davis	f	1000029.0	2024-08-09 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-09 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-09 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-09 16:30:00
Registered Nurse	susan davis	t	\N	2024-08-10 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-10 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-10 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-10 10:30:00
Registered Nurse	susan davis	f	1000020.0	2024-08-10 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-10 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-10 12:00:00
Registered Nurse	susan davis	f	1000034.0	2024-08-10 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-12 08:00:00
Registered Nurse	susan davis	f	1000021.0	2024-08-12 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-12 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-12 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-12 10:00:00
Registered Nurse	susan davis	f	1000099.0	2024-08-12 10:30:00
Registered Nurse	susan davis	f	1000028.0	2024-08-12 11:00:00
Registered Nurse	susan davis	f	1000091.0	2024-08-12 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-12 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-12 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-12 13:00:00
Registered Nurse	susan davis	f	1000073.0	2024-08-12 13:30:00
Registered Nurse	susan davis	f	1000049.0	2024-08-12 14:00:00
Registered Nurse	susan davis	f	1000078.0	2024-08-12 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-12 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-12 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-12 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-12 16:30:00
Registered Nurse	susan davis	f	1000008.0	2024-08-13 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-13 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-13 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-13 09:30:00
Registered Nurse	susan davis	f	1000089.0	2024-08-13 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-13 10:30:00
Registered Nurse	susan davis	f	1000024.0	2024-08-13 11:00:00
Registered Nurse	susan davis	f	1000019.0	2024-08-13 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-13 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-13 12:30:00
Registered Nurse	susan davis	f	1000037.0	2024-08-13 13:00:00
Registered Nurse	susan davis	f	1000085.0	2024-08-13 13:30:00
Registered Nurse	susan davis	f	1000009.0	2024-08-13 14:00:00
Registered Nurse	susan davis	f	1000080.0	2024-08-13 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-13 15:00:00
Registered Nurse	susan davis	f	1000005.0	2024-08-13 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-13 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-13 16:30:00
Registered Nurse	susan davis	t	\N	2024-08-14 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-14 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-14 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-14 09:30:00
Registered Nurse	susan davis	f	1000010.0	2024-08-14 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-14 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-14 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-14 11:30:00
Registered Nurse	susan davis	f	1000006.0	2024-08-14 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-14 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-14 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-14 13:30:00
Registered Nurse	susan davis	f	1000047.0	2024-08-14 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-14 14:30:00
Registered Nurse	susan davis	f	1000030.0	2024-08-14 15:00:00
Registered Nurse	susan davis	f	1000021.0	2024-08-14 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-14 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-14 16:30:00
Registered Nurse	susan davis	f	1000092.0	2024-08-15 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-15 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-15 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-15 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-15 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-15 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-15 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-15 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-15 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-15 12:30:00
Registered Nurse	susan davis	f	1000029.0	2024-08-15 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-15 13:30:00
Registered Nurse	susan davis	t	\N	2024-08-15 14:00:00
Registered Nurse	susan davis	f	1000006.0	2024-08-15 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-15 15:00:00
Registered Nurse	susan davis	f	1000036.0	2024-08-15 15:30:00
Registered Nurse	susan davis	f	1000003.0	2024-08-15 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-15 16:30:00
Registered Nurse	susan davis	t	\N	2024-08-16 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-16 08:30:00
Registered Nurse	susan davis	f	1000055.0	2024-08-16 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-16 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-16 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-16 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-16 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-16 11:30:00
Registered Nurse	susan davis	f	1000066.0	2024-08-16 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-16 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-16 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-16 13:30:00
Registered Nurse	susan davis	t	\N	2024-08-16 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-16 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-16 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-16 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-16 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-16 16:30:00
Registered Nurse	susan davis	t	\N	2024-08-17 09:00:00
Registered Nurse	susan davis	f	1000036.0	2024-08-17 09:30:00
Registered Nurse	susan davis	f	1000091.0	2024-08-17 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-17 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-17 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-17 11:30:00
Registered Nurse	susan davis	f	1000046.0	2024-08-17 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-17 12:30:00
Registered Nurse	susan davis	f	1000015.0	2024-08-19 08:00:00
Registered Nurse	susan davis	f	1000048.0	2024-08-19 08:30:00
Registered Nurse	susan davis	f	1000031.0	2024-08-19 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-19 09:30:00
Registered Nurse	susan davis	f	1000050.0	2024-08-19 10:00:00
Registered Nurse	susan davis	f	1000017.0	2024-08-19 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-19 11:00:00
Registered Nurse	susan davis	f	1000018.0	2024-08-19 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-19 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-19 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-19 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-19 13:30:00
Registered Nurse	susan davis	f	1000096.0	2024-08-19 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-19 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-19 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-19 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-19 16:00:00
Registered Nurse	susan davis	f	1000021.0	2024-08-19 16:30:00
Registered Nurse	susan davis	f	1000077.0	2024-08-20 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-20 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-20 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-20 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-20 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-20 10:30:00
Registered Nurse	susan davis	f	1000025.0	2024-08-20 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-20 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-20 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-20 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-20 13:00:00
Registered Nurse	susan davis	f	1000058.0	2024-08-20 13:30:00
Registered Nurse	susan davis	t	\N	2024-08-20 14:00:00
Registered Nurse	susan davis	f	1000040.0	2024-08-20 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-20 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-20 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-20 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-20 16:30:00
Registered Nurse	susan davis	t	\N	2024-08-21 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-21 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-21 09:00:00
Registered Nurse	susan davis	f	1000048.0	2024-08-21 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-21 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-21 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-21 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-21 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-21 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-21 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-21 13:00:00
Registered Nurse	susan davis	f	1000062.0	2024-08-21 13:30:00
Registered Nurse	susan davis	t	\N	2024-08-21 14:00:00
Registered Nurse	susan davis	f	1000043.0	2024-08-21 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-21 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-21 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-21 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-21 16:30:00
Registered Nurse	susan davis	t	\N	2024-08-22 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-22 08:30:00
Registered Nurse	susan davis	f	1000020.0	2024-08-22 09:00:00
Registered Nurse	susan davis	f	1000045.0	2024-08-22 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-22 10:00:00
Registered Nurse	susan davis	f	1000047.0	2024-08-22 10:30:00
Registered Nurse	susan davis	f	1000029.0	2024-08-22 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-22 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-22 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-22 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-22 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-22 13:30:00
Registered Nurse	susan davis	t	\N	2024-08-22 14:00:00
Registered Nurse	susan davis	f	1000026.0	2024-08-22 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-22 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-22 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-22 16:00:00
Registered Nurse	susan davis	f	1000015.0	2024-08-22 16:30:00
Registered Nurse	susan davis	t	\N	2024-08-23 08:00:00
Registered Nurse	susan davis	f	1000073.0	2024-08-23 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-23 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-23 09:30:00
Registered Nurse	susan davis	f	1000097.0	2024-08-23 10:00:00
Registered Nurse	susan davis	f	1000053.0	2024-08-23 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-23 11:00:00
Registered Nurse	susan davis	f	1000024.0	2024-08-23 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-23 12:00:00
Registered Nurse	susan davis	f	1000006.0	2024-08-23 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-23 13:00:00
Registered Nurse	susan davis	f	1000005.0	2024-08-23 13:30:00
Registered Nurse	susan davis	f	1000054.0	2024-08-23 14:00:00
Registered Nurse	susan davis	f	1000005.0	2024-08-23 14:30:00
Registered Nurse	susan davis	f	1000038.0	2024-08-23 15:00:00
Registered Nurse	susan davis	f	1000090.0	2024-08-23 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-23 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-23 16:30:00
Registered Nurse	susan davis	f	1000028.0	2024-08-24 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-24 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-24 10:00:00
Registered Nurse	susan davis	f	1000070.0	2024-08-24 10:30:00
Registered Nurse	susan davis	f	1000077.0	2024-08-24 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-24 11:30:00
Registered Nurse	susan davis	f	1000007.0	2024-08-24 12:00:00
Registered Nurse	susan davis	f	1000034.0	2024-08-24 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-26 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-26 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-26 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-26 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-26 10:00:00
Registered Nurse	susan davis	f	1000087.0	2024-08-26 10:30:00
Registered Nurse	susan davis	f	1000074.0	2024-08-26 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-26 11:30:00
Registered Nurse	susan davis	f	1000064.0	2024-08-26 12:00:00
Registered Nurse	susan davis	f	1000014.0	2024-08-26 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-26 13:00:00
Registered Nurse	susan davis	f	1000082.0	2024-08-26 13:30:00
Registered Nurse	susan davis	f	1000039.0	2024-08-26 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-26 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-26 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-26 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-26 16:00:00
Registered Nurse	susan davis	f	1000002.0	2024-08-26 16:30:00
Registered Nurse	susan davis	f	1000067.0	2024-08-27 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-27 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-27 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-27 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-27 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-27 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-27 11:00:00
Registered Nurse	susan davis	f	1000047.0	2024-08-27 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-27 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-27 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-27 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-27 13:30:00
Registered Nurse	susan davis	f	1000098.0	2024-08-27 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-27 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-27 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-27 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-27 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-27 16:30:00
Registered Nurse	susan davis	t	\N	2024-08-28 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-28 08:30:00
Registered Nurse	susan davis	f	1000057.0	2024-08-28 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-28 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-28 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-28 10:30:00
Registered Nurse	susan davis	f	1000056.0	2024-08-28 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-28 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-28 12:00:00
Registered Nurse	susan davis	f	1000073.0	2024-08-28 12:30:00
Registered Nurse	susan davis	f	1000017.0	2024-08-28 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-28 13:30:00
Registered Nurse	susan davis	t	\N	2024-08-28 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-28 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-28 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-28 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-28 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-28 16:30:00
Registered Nurse	susan davis	f	1000079.0	2024-08-29 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-29 08:30:00
Registered Nurse	susan davis	f	1000038.0	2024-08-29 09:00:00
Registered Nurse	susan davis	f	1000037.0	2024-08-29 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-29 10:00:00
Registered Nurse	susan davis	f	1000019.0	2024-08-29 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-29 11:00:00
Registered Nurse	susan davis	f	1000017.0	2024-08-29 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-29 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-29 12:30:00
Registered Nurse	susan davis	f	1000066.0	2024-08-29 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-29 13:30:00
Registered Nurse	susan davis	f	1000037.0	2024-08-29 14:00:00
Registered Nurse	susan davis	f	1000045.0	2024-08-29 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-29 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-29 15:30:00
Registered Nurse	susan davis	f	1000008.0	2024-08-29 16:00:00
Registered Nurse	susan davis	t	\N	2024-08-29 16:30:00
Registered Nurse	susan davis	f	1000042.0	2024-08-30 08:00:00
Registered Nurse	susan davis	t	\N	2024-08-30 08:30:00
Registered Nurse	susan davis	t	\N	2024-08-30 09:00:00
Registered Nurse	susan davis	t	\N	2024-08-30 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-30 10:00:00
Registered Nurse	susan davis	f	1000094.0	2024-08-30 10:30:00
Registered Nurse	susan davis	f	1000096.0	2024-08-30 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-30 11:30:00
Registered Nurse	susan davis	f	1000024.0	2024-08-30 12:00:00
Registered Nurse	susan davis	t	\N	2024-08-30 12:30:00
Registered Nurse	susan davis	t	\N	2024-08-30 13:00:00
Registered Nurse	susan davis	t	\N	2024-08-30 13:30:00
Registered Nurse	susan davis	t	\N	2024-08-30 14:00:00
Registered Nurse	susan davis	t	\N	2024-08-30 14:30:00
Registered Nurse	susan davis	t	\N	2024-08-30 15:00:00
Registered Nurse	susan davis	t	\N	2024-08-30 15:30:00
Registered Nurse	susan davis	t	\N	2024-08-30 16:00:00
Registered Nurse	susan davis	f	1000026.0	2024-08-30 16:30:00
Registered Nurse	susan davis	f	1000075.0	2024-08-31 09:00:00
Registered Nurse	susan davis	f	1000021.0	2024-08-31 09:30:00
Registered Nurse	susan davis	t	\N	2024-08-31 10:00:00
Registered Nurse	susan davis	t	\N	2024-08-31 10:30:00
Registered Nurse	susan davis	t	\N	2024-08-31 11:00:00
Registered Nurse	susan davis	t	\N	2024-08-31 11:30:00
Registered Nurse	susan davis	t	\N	2024-08-31 12:00:00
Registered Nurse	susan davis	f	1000010.0	2024-08-31 12:30:00
Registered Nurse	susan davis	t	\N	2024-09-02 08:00:00
Registered Nurse	susan davis	t	\N	2024-09-02 08:30:00
Registered Nurse	susan davis	t	\N	2024-09-02 09:00:00
Registered Nurse	susan davis	t	\N	2024-09-02 09:30:00
Registered Nurse	susan davis	t	\N	2024-09-02 10:00:00
Registered Nurse	susan davis	f	1000007.0	2024-09-02 10:30:00
Registered Nurse	susan davis	t	\N	2024-09-02 11:00:00
Registered Nurse	susan davis	t	\N	2024-09-02 11:30:00
Registered Nurse	susan davis	f	1000072.0	2024-09-02 12:00:00
Registered Nurse	susan davis	t	\N	2024-09-02 12:30:00
Registered Nurse	susan davis	t	\N	2024-09-02 13:00:00
Registered Nurse	susan davis	t	\N	2024-09-02 13:30:00
Registered Nurse	susan davis	t	\N	2024-09-02 14:00:00
Registered Nurse	susan davis	t	\N	2024-09-02 14:30:00
Registered Nurse	susan davis	t	\N	2024-09-02 15:00:00
Registered Nurse	susan davis	f	1000097.0	2024-09-02 15:30:00
Registered Nurse	susan davis	t	\N	2024-09-02 16:00:00
Registered Nurse	susan davis	t	\N	2024-09-02 16:30:00
Registered Nurse	susan davis	f	1000072.0	2024-09-03 08:00:00
Registered Nurse	susan davis	t	\N	2024-09-03 08:30:00
Registered Nurse	susan davis	t	\N	2024-09-03 09:00:00
Registered Nurse	susan davis	f	1000019.0	2024-09-03 09:30:00
Registered Nurse	susan davis	t	\N	2024-09-03 10:00:00
Registered Nurse	susan davis	t	\N	2024-09-03 10:30:00
Registered Nurse	susan davis	t	\N	2024-09-03 11:00:00
Registered Nurse	susan davis	t	\N	2024-09-03 11:30:00
Registered Nurse	susan davis	t	\N	2024-09-03 12:00:00
Registered Nurse	susan davis	t	\N	2024-09-03 12:30:00
Registered Nurse	susan davis	t	\N	2024-09-03 13:00:00
Registered Nurse	susan davis	f	1000020.0	2024-09-03 13:30:00
Registered Nurse	susan davis	t	\N	2024-09-03 14:00:00
Registered Nurse	susan davis	t	\N	2024-09-03 14:30:00
Registered Nurse	susan davis	f	1000049.0	2024-09-03 15:00:00
Registered Nurse	susan davis	f	1000091.0	2024-09-03 15:30:00
Registered Nurse	susan davis	t	\N	2024-09-03 16:00:00
Registered Nurse	susan davis	f	1000048.0	2024-09-03 16:30:00
General Practitioner	kevin anderson	f	1000050.0	2024-08-05 08:00:00
General Practitioner	kevin anderson	f	1000090.0	2024-08-05 08:30:00
General Practitioner	kevin anderson	f	1000057.0	2024-08-05 09:00:00
General Practitioner	kevin anderson	f	1000043.0	2024-08-05 09:30:00
General Practitioner	kevin anderson	f	1000003.0	2024-08-05 10:00:00
General Practitioner	kevin anderson	f	1000010.0	2024-08-05 10:30:00
General Practitioner	kevin anderson	f	1000069.0	2024-08-05 11:00:00
General Practitioner	kevin anderson	f	1000049.0	2024-08-05 11:30:00
General Practitioner	kevin anderson	f	1000080.0	2024-08-05 12:00:00
General Practitioner	kevin anderson	f	1000007.0	2024-08-05 12:30:00
General Practitioner	kevin anderson	f	1000060.0	2024-08-05 13:00:00
General Practitioner	kevin anderson	f	1000063.0	2024-08-05 13:30:00
General Practitioner	kevin anderson	f	1000022.0	2024-08-05 14:00:00
General Practitioner	kevin anderson	f	1000049.0	2024-08-05 14:30:00
General Practitioner	kevin anderson	f	1000060.0	2024-08-05 15:00:00
General Practitioner	kevin anderson	f	1000019.0	2024-08-05 15:30:00
General Practitioner	kevin anderson	f	1000082.0	2024-08-05 16:00:00
General Practitioner	kevin anderson	f	1000083.0	2024-08-05 16:30:00
General Practitioner	kevin anderson	f	1000076.0	2024-08-06 08:00:00
General Practitioner	kevin anderson	f	1000052.0	2024-08-06 08:30:00
General Practitioner	kevin anderson	f	1000061.0	2024-08-06 09:00:00
General Practitioner	kevin anderson	f	1000047.0	2024-08-06 09:30:00
General Practitioner	kevin anderson	f	1000077.0	2024-08-06 10:00:00
General Practitioner	kevin anderson	f	1000085.0	2024-08-06 10:30:00
General Practitioner	kevin anderson	f	1000013.0	2024-08-06 11:00:00
General Practitioner	kevin anderson	f	1000008.0	2024-08-06 11:30:00
General Practitioner	kevin anderson	f	1000054.0	2024-08-06 12:00:00
General Practitioner	kevin anderson	f	1000042.0	2024-08-06 12:30:00
General Practitioner	kevin anderson	f	1000042.0	2024-08-06 13:00:00
General Practitioner	kevin anderson	f	1000054.0	2024-08-06 13:30:00
General Practitioner	kevin anderson	f	1000091.0	2024-08-06 14:00:00
General Practitioner	kevin anderson	f	1000073.0	2024-08-06 14:30:00
General Practitioner	kevin anderson	f	1000058.0	2024-08-06 15:00:00
General Practitioner	kevin anderson	f	1000061.0	2024-08-06 15:30:00
General Practitioner	kevin anderson	f	1000019.0	2024-08-06 16:00:00
General Practitioner	kevin anderson	f	1000021.0	2024-08-06 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-07 08:00:00
General Practitioner	kevin anderson	f	1000085.0	2024-08-07 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-07 09:00:00
General Practitioner	kevin anderson	f	1000065.0	2024-08-07 09:30:00
General Practitioner	kevin anderson	f	1000024.0	2024-08-07 10:00:00
General Practitioner	kevin anderson	f	1000004.0	2024-08-07 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-07 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-07 11:30:00
General Practitioner	kevin anderson	f	1000016.0	2024-08-07 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-07 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-07 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-07 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-07 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-07 14:30:00
General Practitioner	kevin anderson	f	1000000.0	2024-08-07 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-07 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-07 16:00:00
General Practitioner	kevin anderson	f	1000001.0	2024-08-07 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-08 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-08 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-08 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-08 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-08 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-08 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-08 11:00:00
General Practitioner	kevin anderson	f	1000079.0	2024-08-08 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-08 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-08 12:30:00
General Practitioner	kevin anderson	f	1000038.0	2024-08-08 13:00:00
General Practitioner	kevin anderson	f	1000078.0	2024-08-08 13:30:00
General Practitioner	kevin anderson	f	1000040.0	2024-08-08 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-08 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-08 15:00:00
General Practitioner	kevin anderson	f	1000091.0	2024-08-08 15:30:00
General Practitioner	kevin anderson	f	1000029.0	2024-08-08 16:00:00
General Practitioner	kevin anderson	f	1000057.0	2024-08-08 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-09 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-09 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-09 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-09 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-09 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-09 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-09 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-09 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-09 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-09 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-09 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-09 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-09 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-09 14:30:00
General Practitioner	kevin anderson	f	1000022.0	2024-08-09 15:00:00
General Practitioner	kevin anderson	f	1000037.0	2024-08-09 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-09 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-09 16:30:00
General Practitioner	kevin anderson	f	1000056.0	2024-08-10 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-10 09:30:00
General Practitioner	kevin anderson	f	1000092.0	2024-08-10 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-10 10:30:00
General Practitioner	kevin anderson	f	1000099.0	2024-08-10 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-10 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-10 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-10 12:30:00
General Practitioner	kevin anderson	f	1000051.0	2024-08-12 08:00:00
General Practitioner	kevin anderson	f	1000051.0	2024-08-12 08:30:00
General Practitioner	kevin anderson	f	1000059.0	2024-08-12 09:00:00
General Practitioner	kevin anderson	f	1000063.0	2024-08-12 09:30:00
General Practitioner	kevin anderson	f	1000084.0	2024-08-12 10:00:00
General Practitioner	kevin anderson	f	1000079.0	2024-08-12 10:30:00
General Practitioner	kevin anderson	f	1000076.0	2024-08-12 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-12 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-12 12:00:00
General Practitioner	kevin anderson	f	1000088.0	2024-08-12 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-12 13:00:00
General Practitioner	kevin anderson	f	1000034.0	2024-08-12 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-12 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-12 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-12 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-12 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-12 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-12 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-13 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-13 08:30:00
General Practitioner	kevin anderson	f	1000079.0	2024-08-13 09:00:00
General Practitioner	kevin anderson	f	1000020.0	2024-08-13 09:30:00
General Practitioner	kevin anderson	f	1000066.0	2024-08-13 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-13 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-13 11:00:00
General Practitioner	kevin anderson	f	1000027.0	2024-08-13 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-13 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-13 12:30:00
General Practitioner	kevin anderson	f	1000082.0	2024-08-13 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-13 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-13 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-13 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-13 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-13 15:30:00
General Practitioner	kevin anderson	f	1000099.0	2024-08-13 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-13 16:30:00
General Practitioner	kevin anderson	f	1000052.0	2024-08-14 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-14 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-14 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-14 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-14 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-14 10:30:00
General Practitioner	kevin anderson	f	1000082.0	2024-08-14 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-14 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-14 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-14 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-14 13:00:00
General Practitioner	kevin anderson	f	1000038.0	2024-08-14 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-14 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-14 14:30:00
General Practitioner	kevin anderson	f	1000070.0	2024-08-14 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-14 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-14 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-14 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-15 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-15 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-15 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-15 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-15 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-15 10:30:00
General Practitioner	kevin anderson	f	1000066.0	2024-08-15 11:00:00
General Practitioner	kevin anderson	f	1000017.0	2024-08-15 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-15 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-15 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-15 13:00:00
General Practitioner	kevin anderson	f	1000098.0	2024-08-15 13:30:00
General Practitioner	kevin anderson	f	1000093.0	2024-08-15 14:00:00
General Practitioner	kevin anderson	f	1000066.0	2024-08-15 14:30:00
General Practitioner	kevin anderson	f	1000068.0	2024-08-15 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-15 15:30:00
General Practitioner	kevin anderson	f	1000092.0	2024-08-15 16:00:00
General Practitioner	kevin anderson	f	1000083.0	2024-08-15 16:30:00
General Practitioner	kevin anderson	f	1000068.0	2024-08-16 08:00:00
General Practitioner	kevin anderson	f	1000013.0	2024-08-16 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-16 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-16 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-16 10:00:00
General Practitioner	kevin anderson	f	1000030.0	2024-08-16 10:30:00
General Practitioner	kevin anderson	f	1000039.0	2024-08-16 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-16 11:30:00
General Practitioner	kevin anderson	f	1000051.0	2024-08-16 12:00:00
General Practitioner	kevin anderson	f	1000016.0	2024-08-16 12:30:00
General Practitioner	kevin anderson	f	1000021.0	2024-08-16 13:00:00
General Practitioner	kevin anderson	f	1000088.0	2024-08-16 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-16 14:00:00
General Practitioner	kevin anderson	f	1000095.0	2024-08-16 14:30:00
General Practitioner	kevin anderson	f	1000055.0	2024-08-16 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-16 15:30:00
General Practitioner	kevin anderson	f	1000043.0	2024-08-16 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-16 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-17 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-17 09:30:00
General Practitioner	kevin anderson	f	1000056.0	2024-08-17 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-17 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-17 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-17 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-17 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-17 12:30:00
General Practitioner	kevin anderson	f	1000096.0	2024-08-19 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-19 08:30:00
General Practitioner	kevin anderson	f	1000011.0	2024-08-19 09:00:00
General Practitioner	kevin anderson	f	1000013.0	2024-08-19 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-19 10:00:00
General Practitioner	kevin anderson	f	1000076.0	2024-08-19 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-19 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-19 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-19 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-19 12:30:00
General Practitioner	kevin anderson	f	1000061.0	2024-08-19 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-19 13:30:00
General Practitioner	kevin anderson	f	1000085.0	2024-08-19 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-19 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-19 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-19 15:30:00
General Practitioner	kevin anderson	f	1000007.0	2024-08-19 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-19 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-20 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-20 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-20 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-20 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-20 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-20 10:30:00
General Practitioner	kevin anderson	f	1000040.0	2024-08-20 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-20 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-20 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-20 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-20 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-20 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-20 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-20 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-20 15:00:00
General Practitioner	kevin anderson	f	1000058.0	2024-08-20 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-20 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-20 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-21 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-21 08:30:00
General Practitioner	kevin anderson	f	1000020.0	2024-08-21 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-21 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-21 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-21 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-21 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-21 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-21 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-21 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-21 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-21 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-21 14:00:00
General Practitioner	kevin anderson	f	1000032.0	2024-08-21 14:30:00
General Practitioner	kevin anderson	f	1000031.0	2024-08-21 15:00:00
General Practitioner	kevin anderson	f	1000017.0	2024-08-21 15:30:00
General Practitioner	kevin anderson	f	1000005.0	2024-08-21 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-21 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-22 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-22 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-22 09:00:00
General Practitioner	kevin anderson	f	1000054.0	2024-08-22 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-22 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-22 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-22 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-22 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-22 12:00:00
General Practitioner	kevin anderson	f	1000064.0	2024-08-22 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-22 13:00:00
General Practitioner	kevin anderson	f	1000041.0	2024-08-22 13:30:00
General Practitioner	kevin anderson	f	1000078.0	2024-08-22 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-22 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-22 15:00:00
General Practitioner	kevin anderson	f	1000055.0	2024-08-22 15:30:00
General Practitioner	kevin anderson	f	1000078.0	2024-08-22 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-22 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-23 08:00:00
General Practitioner	kevin anderson	f	1000050.0	2024-08-23 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-23 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-23 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-23 10:00:00
General Practitioner	kevin anderson	f	1000051.0	2024-08-23 10:30:00
General Practitioner	kevin anderson	f	1000002.0	2024-08-23 11:00:00
General Practitioner	kevin anderson	f	1000006.0	2024-08-23 11:30:00
General Practitioner	kevin anderson	f	1000053.0	2024-08-23 12:00:00
General Practitioner	kevin anderson	f	1000020.0	2024-08-23 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-23 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-23 13:30:00
General Practitioner	kevin anderson	f	1000075.0	2024-08-23 14:00:00
General Practitioner	kevin anderson	f	1000016.0	2024-08-23 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-23 15:00:00
General Practitioner	kevin anderson	f	1000071.0	2024-08-23 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-23 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-23 16:30:00
General Practitioner	kevin anderson	f	1000022.0	2024-08-24 09:00:00
General Practitioner	kevin anderson	f	1000095.0	2024-08-24 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-24 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-24 10:30:00
General Practitioner	kevin anderson	f	1000099.0	2024-08-24 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-24 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-24 12:00:00
General Practitioner	kevin anderson	f	1000015.0	2024-08-24 12:30:00
General Practitioner	kevin anderson	f	1000015.0	2024-08-26 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-26 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-26 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-26 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-26 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-26 10:30:00
General Practitioner	kevin anderson	f	1000087.0	2024-08-26 11:00:00
General Practitioner	kevin anderson	f	1000050.0	2024-08-26 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-26 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-26 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-26 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-26 13:30:00
General Practitioner	kevin anderson	f	1000067.0	2024-08-26 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-26 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-26 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-26 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-26 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-26 16:30:00
General Practitioner	kevin anderson	f	1000032.0	2024-08-27 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-27 08:30:00
General Practitioner	kevin anderson	f	1000038.0	2024-08-27 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-27 09:30:00
General Practitioner	kevin anderson	f	1000036.0	2024-08-27 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-27 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-27 11:00:00
General Practitioner	kevin anderson	f	1000071.0	2024-08-27 11:30:00
General Practitioner	kevin anderson	f	1000046.0	2024-08-27 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-27 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-27 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-27 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-27 14:00:00
General Practitioner	kevin anderson	f	1000040.0	2024-08-27 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-27 15:00:00
General Practitioner	kevin anderson	f	1000093.0	2024-08-27 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-27 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-27 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-28 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-28 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-28 09:00:00
General Practitioner	kevin anderson	f	1000016.0	2024-08-28 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-28 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-28 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-28 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-28 11:30:00
General Practitioner	kevin anderson	t	\N	2024-08-28 12:00:00
General Practitioner	kevin anderson	f	1000008.0	2024-08-28 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-28 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-28 13:30:00
General Practitioner	kevin anderson	f	1000003.0	2024-08-28 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-28 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-28 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-28 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-28 16:00:00
General Practitioner	kevin anderson	f	1000085.0	2024-08-28 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-29 08:00:00
General Practitioner	kevin anderson	f	1000003.0	2024-08-29 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-29 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-29 09:30:00
General Practitioner	kevin anderson	t	\N	2024-08-29 10:00:00
General Practitioner	kevin anderson	f	1000011.0	2024-08-29 10:30:00
General Practitioner	kevin anderson	f	1000089.0	2024-08-29 11:00:00
General Practitioner	kevin anderson	f	1000028.0	2024-08-29 11:30:00
General Practitioner	kevin anderson	f	1000020.0	2024-08-29 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-29 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-29 13:00:00
General Practitioner	kevin anderson	t	\N	2024-08-29 13:30:00
General Practitioner	kevin anderson	t	\N	2024-08-29 14:00:00
General Practitioner	kevin anderson	f	1000005.0	2024-08-29 14:30:00
General Practitioner	kevin anderson	t	\N	2024-08-29 15:00:00
General Practitioner	kevin anderson	f	1000010.0	2024-08-29 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-29 16:00:00
General Practitioner	kevin anderson	t	\N	2024-08-29 16:30:00
General Practitioner	kevin anderson	t	\N	2024-08-30 08:00:00
General Practitioner	kevin anderson	t	\N	2024-08-30 08:30:00
General Practitioner	kevin anderson	t	\N	2024-08-30 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-30 09:30:00
General Practitioner	kevin anderson	f	1000053.0	2024-08-30 10:00:00
General Practitioner	kevin anderson	t	\N	2024-08-30 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-30 11:00:00
General Practitioner	kevin anderson	t	\N	2024-08-30 11:30:00
General Practitioner	kevin anderson	f	1000050.0	2024-08-30 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-30 12:30:00
General Practitioner	kevin anderson	t	\N	2024-08-30 13:00:00
General Practitioner	kevin anderson	f	1000029.0	2024-08-30 13:30:00
General Practitioner	kevin anderson	f	1000089.0	2024-08-30 14:00:00
General Practitioner	kevin anderson	t	\N	2024-08-30 14:30:00
General Practitioner	kevin anderson	f	1000018.0	2024-08-30 15:00:00
General Practitioner	kevin anderson	t	\N	2024-08-30 15:30:00
General Practitioner	kevin anderson	t	\N	2024-08-30 16:00:00
General Practitioner	kevin anderson	f	1000018.0	2024-08-30 16:30:00
General Practitioner	kevin anderson	f	1000040.0	2024-08-31 09:00:00
General Practitioner	kevin anderson	t	\N	2024-08-31 09:30:00
General Practitioner	kevin anderson	f	1000019.0	2024-08-31 10:00:00
General Practitioner	kevin anderson	f	1000079.0	2024-08-31 10:30:00
General Practitioner	kevin anderson	t	\N	2024-08-31 11:00:00
General Practitioner	kevin anderson	f	1000033.0	2024-08-31 11:30:00
General Practitioner	kevin anderson	f	1000087.0	2024-08-31 12:00:00
General Practitioner	kevin anderson	t	\N	2024-08-31 12:30:00
General Practitioner	kevin anderson	f	1000051.0	2024-09-02 08:00:00
General Practitioner	kevin anderson	t	\N	2024-09-02 08:30:00
General Practitioner	kevin anderson	t	\N	2024-09-02 09:00:00
General Practitioner	kevin anderson	f	1000068.0	2024-09-02 09:30:00
General Practitioner	kevin anderson	t	\N	2024-09-02 10:00:00
General Practitioner	kevin anderson	t	\N	2024-09-02 10:30:00
General Practitioner	kevin anderson	t	\N	2024-09-02 11:00:00
General Practitioner	kevin anderson	t	\N	2024-09-02 11:30:00
General Practitioner	kevin anderson	f	1000071.0	2024-09-02 12:00:00
General Practitioner	kevin anderson	t	\N	2024-09-02 12:30:00
General Practitioner	kevin anderson	t	\N	2024-09-02 13:00:00
General Practitioner	kevin anderson	t	\N	2024-09-02 13:30:00
General Practitioner	kevin anderson	f	1000007.0	2024-09-02 14:00:00
General Practitioner	kevin anderson	t	\N	2024-09-02 14:30:00
General Practitioner	kevin anderson	t	\N	2024-09-02 15:00:00
General Practitioner	kevin anderson	t	\N	2024-09-02 15:30:00
General Practitioner	kevin anderson	t	\N	2024-09-02 16:00:00
General Practitioner	kevin anderson	t	\N	2024-09-02 16:30:00
General Practitioner	kevin anderson	t	\N	2024-09-03 08:00:00
General Practitioner	kevin anderson	t	\N	2024-09-03 08:30:00
General Practitioner	kevin anderson	f	1000015.0	2024-09-03 09:00:00
General Practitioner	kevin anderson	f	1000060.0	2024-09-03 09:30:00
General Practitioner	kevin anderson	f	1000100.0	2024-09-03 10:00:00
General Practitioner	kevin anderson	f	1000034.0	2024-09-03 10:30:00
General Practitioner	kevin anderson	f	1000076.0	2024-09-03 11:00:00
General Practitioner	kevin anderson	t	\N	2024-09-03 11:30:00
General Practitioner	kevin anderson	t	\N	2024-09-03 12:00:00
General Practitioner	kevin anderson	t	\N	2024-09-03 12:30:00
General Practitioner	kevin anderson	t	\N	2024-09-03 13:00:00
General Practitioner	kevin anderson	f	1000023.0	2024-09-03 13:30:00
General Practitioner	kevin anderson	t	\N	2024-09-03 14:00:00
General Practitioner	kevin anderson	t	\N	2024-09-03 14:30:00
General Practitioner	kevin anderson	t	\N	2024-09-03 15:00:00
General Practitioner	kevin anderson	t	\N	2024-09-03 15:30:00
General Practitioner	kevin anderson	t	\N	2024-09-03 16:00:00
General Practitioner	kevin anderson	t	\N	2024-09-03 16:30:00
Geriatrician	daniel miller	f	1000074.0	2024-08-05 08:30:00
Geriatrician	daniel miller	f	1000092.0	2024-08-05 09:00:00
Geriatrician	daniel miller	f	1000090.0	2024-08-05 09:30:00
Geriatrician	daniel miller	f	1000033.0	2024-08-05 10:00:00
Geriatrician	daniel miller	f	1000049.0	2024-08-05 10:30:00
Geriatrician	daniel miller	f	1000040.0	2024-08-05 11:00:00
Geriatrician	daniel miller	f	1000008.0	2024-08-05 11:30:00
Geriatrician	daniel miller	f	1000070.0	2024-08-05 12:00:00
Geriatrician	daniel miller	f	1000080.0	2024-08-05 12:30:00
Geriatrician	daniel miller	f	1000087.0	2024-08-05 13:00:00
Geriatrician	daniel miller	f	1000006.0	2024-08-05 13:30:00
Geriatrician	daniel miller	f	1000004.0	2024-08-05 14:00:00
Geriatrician	daniel miller	f	1000030.0	2024-08-05 14:30:00
Geriatrician	daniel miller	f	1000009.0	2024-08-05 15:00:00
Geriatrician	daniel miller	f	1000006.0	2024-08-05 15:30:00
Geriatrician	daniel miller	f	1000000.0	2024-08-05 16:00:00
Geriatrician	daniel miller	f	1000047.0	2024-08-05 16:30:00
Geriatrician	daniel miller	f	1000098.0	2024-08-06 08:00:00
Geriatrician	daniel miller	f	1000092.0	2024-08-06 08:30:00
Geriatrician	daniel miller	f	1000015.0	2024-08-06 09:00:00
Geriatrician	daniel miller	f	1000028.0	2024-08-06 09:30:00
Geriatrician	daniel miller	f	1000027.0	2024-08-06 10:00:00
Geriatrician	daniel miller	f	1000065.0	2024-08-06 10:30:00
Geriatrician	daniel miller	f	1000023.0	2024-08-06 11:00:00
Geriatrician	daniel miller	f	1000095.0	2024-08-06 11:30:00
Geriatrician	daniel miller	f	1000053.0	2024-08-06 12:00:00
Geriatrician	daniel miller	f	1000055.0	2024-08-06 12:30:00
Geriatrician	daniel miller	f	1000085.0	2024-08-06 13:00:00
Geriatrician	daniel miller	f	1000092.0	2024-08-06 13:30:00
Geriatrician	daniel miller	f	1000014.0	2024-08-06 14:00:00
Geriatrician	daniel miller	f	1000075.0	2024-08-06 14:30:00
Geriatrician	daniel miller	f	1000065.0	2024-08-06 15:00:00
Geriatrician	daniel miller	f	1000000.0	2024-08-06 15:30:00
Geriatrician	daniel miller	f	1000030.0	2024-08-06 16:00:00
Geriatrician	daniel miller	f	1000018.0	2024-08-06 16:30:00
Geriatrician	daniel miller	f	1000006.0	2024-08-07 08:00:00
Geriatrician	daniel miller	f	1000068.0	2024-08-07 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-07 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-07 09:30:00
Geriatrician	daniel miller	f	1000067.0	2024-08-07 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-07 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-07 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-07 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-07 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-07 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-07 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-07 13:30:00
Geriatrician	daniel miller	f	1000083.0	2024-08-07 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-07 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-07 15:00:00
Geriatrician	daniel miller	f	1000029.0	2024-08-07 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-07 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-07 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-08 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-08 08:30:00
Geriatrician	daniel miller	f	1000045.0	2024-08-08 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-08 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-08 10:00:00
Geriatrician	daniel miller	f	1000065.0	2024-08-08 10:30:00
Geriatrician	daniel miller	f	1000040.0	2024-08-08 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-08 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-08 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-08 12:30:00
Geriatrician	daniel miller	f	1000049.0	2024-08-08 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-08 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-08 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-08 14:30:00
Geriatrician	daniel miller	f	1000023.0	2024-08-08 15:00:00
Geriatrician	daniel miller	t	\N	2024-08-08 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-08 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-08 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-09 08:00:00
Geriatrician	daniel miller	f	1000062.0	2024-08-09 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-09 09:00:00
Geriatrician	daniel miller	f	1000021.0	2024-08-09 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-09 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-09 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-09 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-09 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-09 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-09 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-09 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-09 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-09 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-09 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-09 15:00:00
Geriatrician	daniel miller	t	\N	2024-08-09 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-09 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-09 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-10 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-10 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-10 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-10 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-10 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-10 11:30:00
Geriatrician	daniel miller	f	1000057.0	2024-08-10 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-10 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-12 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-12 08:30:00
Geriatrician	daniel miller	f	1000055.0	2024-08-12 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-12 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-12 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-12 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-12 11:00:00
Geriatrician	daniel miller	f	1000075.0	2024-08-12 11:30:00
Geriatrician	daniel miller	f	1000015.0	2024-08-12 12:00:00
Geriatrician	daniel miller	f	1000023.0	2024-08-12 12:30:00
Geriatrician	daniel miller	f	1000043.0	2024-08-12 13:00:00
Geriatrician	daniel miller	f	1000095.0	2024-08-12 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-12 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-12 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-12 15:00:00
Geriatrician	daniel miller	t	\N	2024-08-12 15:30:00
Geriatrician	daniel miller	f	1000031.0	2024-08-12 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-12 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-13 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-13 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-13 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-13 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-13 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-13 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-13 11:00:00
Geriatrician	daniel miller	f	1000026.0	2024-08-13 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-13 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-13 12:30:00
Geriatrician	daniel miller	f	1000036.0	2024-08-13 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-13 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-13 14:00:00
Geriatrician	daniel miller	f	1000011.0	2024-08-13 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-13 15:00:00
Geriatrician	daniel miller	f	1000027.0	2024-08-13 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-13 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-13 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-14 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-14 08:30:00
Geriatrician	daniel miller	f	1000064.0	2024-08-14 09:00:00
Geriatrician	daniel miller	f	1000075.0	2024-08-14 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-14 10:00:00
Geriatrician	daniel miller	f	1000004.0	2024-08-14 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-14 11:00:00
Geriatrician	daniel miller	f	1000029.0	2024-08-14 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-14 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-14 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-14 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-14 13:30:00
Geriatrician	daniel miller	f	1000058.0	2024-08-14 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-14 14:30:00
Geriatrician	daniel miller	f	1000030.0	2024-08-14 15:00:00
Geriatrician	daniel miller	f	1000048.0	2024-08-14 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-14 16:00:00
Geriatrician	daniel miller	f	1000052.0	2024-08-14 16:30:00
Geriatrician	daniel miller	f	1000009.0	2024-08-15 08:00:00
Geriatrician	daniel miller	f	1000019.0	2024-08-15 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-15 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-15 09:30:00
Geriatrician	daniel miller	f	1000072.0	2024-08-15 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-15 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-15 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-15 11:30:00
Geriatrician	daniel miller	f	1000020.0	2024-08-15 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-15 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-15 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-15 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-15 14:00:00
Geriatrician	daniel miller	f	1000053.0	2024-08-15 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-15 15:00:00
Geriatrician	daniel miller	f	1000085.0	2024-08-15 15:30:00
Geriatrician	daniel miller	f	1000063.0	2024-08-15 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-15 16:30:00
Geriatrician	daniel miller	f	1000011.0	2024-08-16 08:00:00
Geriatrician	daniel miller	f	1000073.0	2024-08-16 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-16 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-16 09:30:00
Geriatrician	daniel miller	f	1000017.0	2024-08-16 10:00:00
Geriatrician	daniel miller	f	1000099.0	2024-08-16 10:30:00
Geriatrician	daniel miller	f	1000016.0	2024-08-16 11:00:00
Geriatrician	daniel miller	f	1000039.0	2024-08-16 11:30:00
Geriatrician	daniel miller	f	1000010.0	2024-08-16 12:00:00
Geriatrician	daniel miller	f	1000061.0	2024-08-16 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-16 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-16 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-16 14:00:00
Geriatrician	daniel miller	f	1000028.0	2024-08-16 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-16 15:00:00
Geriatrician	daniel miller	t	\N	2024-08-16 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-16 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-16 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-17 09:00:00
Geriatrician	daniel miller	f	1000055.0	2024-08-17 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-17 10:00:00
Geriatrician	daniel miller	f	1000028.0	2024-08-17 10:30:00
Geriatrician	daniel miller	f	1000071.0	2024-08-17 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-17 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-17 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-17 12:30:00
Geriatrician	daniel miller	f	1000092.0	2024-08-19 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-19 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-19 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-19 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-19 10:00:00
Geriatrician	daniel miller	f	1000007.0	2024-08-19 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-19 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-19 11:30:00
Geriatrician	daniel miller	f	1000088.0	2024-08-19 12:00:00
Geriatrician	daniel miller	f	1000071.0	2024-08-19 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-19 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-19 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-19 14:00:00
Geriatrician	daniel miller	f	1000085.0	2024-08-19 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-19 15:00:00
Geriatrician	daniel miller	t	\N	2024-08-19 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-19 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-19 16:30:00
Geriatrician	daniel miller	f	1000052.0	2024-08-20 08:00:00
Geriatrician	daniel miller	f	1000004.0	2024-08-20 08:30:00
Geriatrician	daniel miller	f	1000072.0	2024-08-20 09:00:00
Geriatrician	daniel miller	f	1000065.0	2024-08-20 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-20 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-20 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-20 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-20 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-20 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-20 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-20 13:00:00
Geriatrician	daniel miller	f	1000090.0	2024-08-20 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-20 14:00:00
Geriatrician	daniel miller	f	1000079.0	2024-08-20 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-20 15:00:00
Geriatrician	daniel miller	t	\N	2024-08-20 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-20 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-20 16:30:00
Geriatrician	daniel miller	f	1000084.0	2024-08-21 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-21 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-21 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-21 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-21 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-21 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-21 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-21 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-21 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-21 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-21 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-21 13:30:00
Geriatrician	daniel miller	f	1000059.0	2024-08-21 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-21 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-21 15:00:00
Geriatrician	daniel miller	t	\N	2024-08-21 15:30:00
Geriatrician	daniel miller	f	1000014.0	2024-08-21 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-21 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-22 08:00:00
Geriatrician	daniel miller	f	1000076.0	2024-08-22 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-22 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-22 09:30:00
Geriatrician	daniel miller	f	1000081.0	2024-08-22 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-22 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-22 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-22 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-22 12:00:00
Geriatrician	daniel miller	f	1000073.0	2024-08-22 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-22 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-22 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-22 14:00:00
Geriatrician	daniel miller	f	1000005.0	2024-08-22 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-22 15:00:00
Geriatrician	daniel miller	f	1000092.0	2024-08-22 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-22 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-22 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-23 08:00:00
Geriatrician	daniel miller	f	1000010.0	2024-08-23 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-23 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-23 09:30:00
Geriatrician	daniel miller	f	1000077.0	2024-08-23 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-23 10:30:00
Geriatrician	daniel miller	f	1000008.0	2024-08-23 11:00:00
Geriatrician	daniel miller	f	1000008.0	2024-08-23 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-23 12:00:00
Geriatrician	daniel miller	f	1000098.0	2024-08-23 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-23 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-23 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-23 14:00:00
Geriatrician	daniel miller	f	1000087.0	2024-08-23 14:30:00
Geriatrician	daniel miller	f	1000046.0	2024-08-23 15:00:00
Geriatrician	daniel miller	f	1000052.0	2024-08-23 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-23 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-23 16:30:00
Geriatrician	daniel miller	f	1000099.0	2024-08-24 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-24 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-24 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-24 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-24 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-24 11:30:00
Geriatrician	daniel miller	f	1000062.0	2024-08-24 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-24 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-26 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-26 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-26 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-26 09:30:00
Geriatrician	daniel miller	f	1000077.0	2024-08-26 10:00:00
Geriatrician	daniel miller	f	1000027.0	2024-08-26 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-26 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-26 11:30:00
Geriatrician	daniel miller	f	1000014.0	2024-08-26 12:00:00
Geriatrician	daniel miller	f	1000039.0	2024-08-26 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-26 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-26 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-26 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-26 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-26 15:00:00
Geriatrician	daniel miller	f	1000013.0	2024-08-26 15:30:00
Geriatrician	daniel miller	f	1000098.0	2024-08-26 16:00:00
Geriatrician	daniel miller	f	1000069.0	2024-08-26 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-27 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-27 08:30:00
Geriatrician	daniel miller	f	1000056.0	2024-08-27 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-27 09:30:00
Geriatrician	daniel miller	f	1000022.0	2024-08-27 10:00:00
Geriatrician	daniel miller	f	1000064.0	2024-08-27 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-27 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-27 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-27 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-27 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-27 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-27 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-27 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-27 14:30:00
Geriatrician	daniel miller	f	1000041.0	2024-08-27 15:00:00
Geriatrician	daniel miller	f	1000093.0	2024-08-27 15:30:00
Geriatrician	daniel miller	f	1000044.0	2024-08-27 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-27 16:30:00
Geriatrician	daniel miller	f	1000017.0	2024-08-28 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-28 08:30:00
Geriatrician	daniel miller	f	1000075.0	2024-08-28 09:00:00
Geriatrician	daniel miller	f	1000034.0	2024-08-28 09:30:00
Geriatrician	daniel miller	f	1000041.0	2024-08-28 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-28 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-28 11:00:00
Geriatrician	daniel miller	f	1000074.0	2024-08-28 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-28 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-28 12:30:00
Geriatrician	daniel miller	f	1000087.0	2024-08-28 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-28 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-28 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-28 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-28 15:00:00
Geriatrician	daniel miller	f	1000075.0	2024-08-28 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-28 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-28 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-29 08:00:00
Geriatrician	daniel miller	f	1000074.0	2024-08-29 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-29 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-29 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-29 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-29 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-29 11:00:00
Geriatrician	daniel miller	f	1000051.0	2024-08-29 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-29 12:00:00
Geriatrician	daniel miller	f	1000053.0	2024-08-29 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-29 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-29 13:30:00
Geriatrician	daniel miller	t	\N	2024-08-29 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-29 14:30:00
Geriatrician	daniel miller	t	\N	2024-08-29 15:00:00
Geriatrician	daniel miller	f	1000031.0	2024-08-29 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-29 16:00:00
Geriatrician	daniel miller	t	\N	2024-08-29 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-30 08:00:00
Geriatrician	daniel miller	t	\N	2024-08-30 08:30:00
Geriatrician	daniel miller	t	\N	2024-08-30 09:00:00
Geriatrician	daniel miller	t	\N	2024-08-30 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-30 10:00:00
Geriatrician	daniel miller	t	\N	2024-08-30 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-30 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-30 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-30 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-30 12:30:00
Geriatrician	daniel miller	t	\N	2024-08-30 13:00:00
Geriatrician	daniel miller	t	\N	2024-08-30 13:30:00
Geriatrician	daniel miller	f	1000052.0	2024-08-30 14:00:00
Geriatrician	daniel miller	t	\N	2024-08-30 14:30:00
Geriatrician	daniel miller	f	1000094.0	2024-08-30 15:00:00
Geriatrician	daniel miller	f	1000030.0	2024-08-30 15:30:00
Geriatrician	daniel miller	t	\N	2024-08-30 16:00:00
Geriatrician	daniel miller	f	1000100.0	2024-08-30 16:30:00
Geriatrician	daniel miller	t	\N	2024-08-31 09:00:00
Geriatrician	daniel miller	f	1000027.0	2024-08-31 09:30:00
Geriatrician	daniel miller	t	\N	2024-08-31 10:00:00
Geriatrician	daniel miller	f	1000024.0	2024-08-31 10:30:00
Geriatrician	daniel miller	t	\N	2024-08-31 11:00:00
Geriatrician	daniel miller	t	\N	2024-08-31 11:30:00
Geriatrician	daniel miller	t	\N	2024-08-31 12:00:00
Geriatrician	daniel miller	t	\N	2024-08-31 12:30:00
Geriatrician	daniel miller	f	1000003.0	2024-09-02 08:00:00
Geriatrician	daniel miller	t	\N	2024-09-02 08:30:00
Geriatrician	daniel miller	t	\N	2024-09-02 09:00:00
Geriatrician	daniel miller	f	1000070.0	2024-09-02 09:30:00
Geriatrician	daniel miller	t	\N	2024-09-02 10:00:00
Geriatrician	daniel miller	t	\N	2024-09-02 10:30:00
Geriatrician	daniel miller	t	\N	2024-09-02 11:00:00
Geriatrician	daniel miller	t	\N	2024-09-02 11:30:00
Geriatrician	daniel miller	t	\N	2024-09-02 12:00:00
Geriatrician	daniel miller	f	1000036.0	2024-09-02 12:30:00
Geriatrician	daniel miller	t	\N	2024-09-02 13:00:00
Geriatrician	daniel miller	t	\N	2024-09-02 13:30:00
Geriatrician	daniel miller	t	\N	2024-09-02 14:00:00
Geriatrician	daniel miller	t	\N	2024-09-02 14:30:00
Geriatrician	daniel miller	t	\N	2024-09-02 15:00:00
Geriatrician	daniel miller	t	\N	2024-09-02 15:30:00
Geriatrician	daniel miller	t	\N	2024-09-02 16:00:00
Geriatrician	daniel miller	f	1000052.0	2024-09-02 16:30:00
Geriatrician	daniel miller	f	1000023.0	2024-09-03 08:00:00
Geriatrician	daniel miller	t	\N	2024-09-03 08:30:00
Geriatrician	daniel miller	t	\N	2024-09-03 09:00:00
Geriatrician	daniel miller	t	\N	2024-09-03 09:30:00
Geriatrician	daniel miller	t	\N	2024-09-03 10:00:00
Geriatrician	daniel miller	f	1000004.0	2024-09-03 10:30:00
Pharmacist	michael green	f	1000067.0	2024-08-30 15:00:00
Pharmacist	michael green	t	\N	2024-08-30 15:30:00
Pharmacist	michael green	f	1000048.0	2024-08-30 16:00:00
Pharmacist	michael green	f	1000071.0	2024-08-30 16:30:00
Pharmacist	michael green	f	1000074.0	2024-08-31 09:00:00
Pharmacist	michael green	t	\N	2024-08-31 09:30:00
Pharmacist	michael green	t	\N	2024-08-31 10:00:00
Pharmacist	michael green	t	\N	2024-08-31 10:30:00
Pharmacist	michael green	t	\N	2024-08-31 11:00:00
Pharmacist	michael green	f	1000055.0	2024-08-31 11:30:00
Pharmacist	michael green	t	\N	2024-08-31 12:00:00
Pharmacist	michael green	t	\N	2024-08-31 12:30:00
Pharmacist	michael green	t	\N	2024-09-02 08:00:00
Pharmacist	michael green	t	\N	2024-09-02 08:30:00
Pharmacist	michael green	f	1000043.0	2024-09-02 09:00:00
Pharmacist	michael green	f	1000015.0	2024-09-02 09:30:00
Pharmacist	michael green	t	\N	2024-09-02 10:00:00
Pharmacist	michael green	t	\N	2024-09-02 10:30:00
Pharmacist	michael green	t	\N	2024-09-02 11:00:00
Pharmacist	michael green	t	\N	2024-09-02 11:30:00
Pharmacist	michael green	t	\N	2024-09-02 12:00:00
Pharmacist	michael green	t	\N	2024-09-02 12:30:00
Pharmacist	michael green	f	1000019.0	2024-09-02 13:00:00
Pharmacist	michael green	t	\N	2024-09-02 13:30:00
Pharmacist	michael green	f	1000100.0	2024-09-02 14:00:00
Pharmacist	michael green	t	\N	2024-09-02 14:30:00
Pharmacist	michael green	t	\N	2024-09-02 15:00:00
\.


--
-- PostgreSQL database dump complete
--

