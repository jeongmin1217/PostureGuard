ALTER TABLE postureguard-432006.dataset_pg.tb_posture DROP COLUMN timestamp;
ALTER TABLE postureguard-432006.dataset_pg.tb_posture ADD COLUMN timestamp STRING;

ALTER TABLE postureguard-432006.dataset_pg.tb_image DROP COLUMN capture_time;
ALTER TABLE postureguard-432006.dataset_pg.tb_image ADD COLUMN capture_time STRING;

ALTER TABLE postureguard-432006.dataset_pg.tb_day DROP COLUMN day_value;
ALTER TABLE postureguard-432006.dataset_pg.tb_day ADD COLUMN day_value STRING;

