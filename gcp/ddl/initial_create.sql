CREATE TABLE postureguard-432006.dataset_pg.tb_posture (
    posture_id STRING NOT NULL,
    img_filename STRING NOT NULL,
    cva_left_value FLOAT64,
    cva_right_value FLOAT64,
    fha_left_value FLOAT64,
    fha_right_value FLOAT64,
    posture_status BOOLEAN,  -- BOOLEAN 타입으로 설정
    user_id STRING NOT NULL,
    day_id INTEGER,
    week_id INTEGER,
    month_id INTEGER,
    year_id INTEGER,
    timestamp TIMESTAMP
)
PARTITION BY DATE(timestamp);  -- 일별 파티셔닝

CREATE TABLE postureguard-432006.dataset_pg.tb_image (
    img_id STRING NOT NULL,
    img_filename STRING NOT NULL,
    capture_time TIMESTAMP,
    file_size INTEGER
);

CREATE TABLE postureguard-432006.dataset_pg.tb_user (
    user_id STRING NOT NULL,
    user_name STRING,
    user_age INTEGER,
    user_gender STRING
);

CREATE TABLE postureguard-432006.dataset_pg.tb_year (
    year_id INTEGER, -- 기본 키
    year_value INTEGER -- 연도 값 (예: 2024)
);

CREATE TABLE postureguard-432006.dataset_pg.tb_month (
    month_id INTEGER, -- 기본 키
    month_value STRING, -- 월 이름 (예: January, February)
    year_id INTEGER -- 연도와 연결하기 위한 외래 키
);

CREATE TABLE postureguard-432006.dataset_pg.tb_day (
    day_id INTEGER, -- 기본 키
    day_value DATE, -- 일별 날짜 값 (예: 2024-08-14)
    month_id INTEGER, -- 월과 연결하기 위한 외래 키
    week_id INTEGER -- 주와 연결하기 위한 외래 키 (선택 사항)
);

CREATE TABLE postureguard-432006.dataset_pg.tb_week (
    week_id INTEGER, -- 기본 키
    week_value INTEGER, -- 주 번호 (예: 34번째 주)
    year_id INTEGER -- 연도와 연결하기 위한 외래 키
);

CREATE TABLE postureguard-432006.dataset_pg.tb_daily_stat (
    daily_stat_id STRING, -- 기본 키
    year_id INTEGER, -- 
    month_id INTEGER, -- 
    day_id INTEGER, --
    avg_left_shoulder_x FLOAT64, -- 
    avg_left_shoulder_y FLOAT64, -- 
    avg_right_shoulder_x FLOAT64, -- 
    avg_right_shoulder_y FLOAT64, -- 
    avg_left_ear_x FLOAT64, -- 
    avg_left_ear_y FLOAT64, -- 
    avg_right_ear_x FLOAT64, -- 
    avg_right_ear_y FLOAT64, -- 
    avg_c7_x FLOAT64, -- 
    avg_c7_y FLOAT64, -- 
    posture_correct BOOLEAN, --
    img_filename STRING, --
    cnt INTEGER
);

ALTER TABLE postureguard-432006.dataset_pg.tb_daily_stat
ADD COLUMN avg_left_shoulder_z FLOAT64;
ALTER TABLE postureguard-432006.dataset_pg.tb_daily_stat
ADD COLUMN avg_right_shoulder_z FLOAT64;
ALTER TABLE postureguard-432006.dataset_pg.tb_daily_stat
ADD COLUMN avg_left_ear_z FLOAT64;
ALTER TABLE postureguard-432006.dataset_pg.tb_daily_stat
ADD COLUMN avg_right_ear_z FLOAT64;
ALTER TABLE postureguard-432006.dataset_pg.tb_daily_stat
ADD COLUMN avg_c7_z FLOAT64;
