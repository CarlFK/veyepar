SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL';

CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci ;
USE `mydb`;

-- -----------------------------------------------------
-- Table `mydb`.`episode`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`episode` ;

CREATE  TABLE IF NOT EXISTS `mydb`.`episode` (
  `id` INT NOT NULL ,
  `name` VARCHAR(45) NOT NULL ,
  `description` TEXT NULL ,
  `start` DATETIME NULL ,
  `end` DATETIME NULL ,
  `location_id` INT NOT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_event_location` (`location_id` ASC) ,
  CONSTRAINT `fk_event_location`
    FOREIGN KEY (`location_id` )
    REFERENCES `mydb`.`location` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'somethng that would be watched. a talk.';


-- -----------------------------------------------------
-- Table `mydb`.`location`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`location` ;

CREATE  TABLE IF NOT EXISTS `mydb`.`location` (
  `id` INT NOT NULL ,
  `name` VARCHAR(45) NOT NULL ,
  INDEX `fk_log_event` (`id` ASC) ,
  PRIMARY KEY (`id`) ,
  CONSTRAINT `fk_log_event`
    FOREIGN KEY (`id` )
    REFERENCES `mydb`.`episode` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`raw_file`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`raw_file` ;

CREATE  TABLE IF NOT EXISTS `mydb`.`raw_file` (
  `id` INT NOT NULL ,
  `filename` VARCHAR(45) NOT NULL ,
  `location_id` INT NOT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_raw_file_location` (`location_id` ASC) ,
  CONSTRAINT `fk_raw_file_location`
    FOREIGN KEY (`location_id` )
    REFERENCES `mydb`.`location` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`cutlist`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`cutlist` ;

CREATE  TABLE IF NOT EXISTS `mydb`.`cutlist` (
  `id` INT NOT NULL ,
  `sequence` INT NOT NULL ,
  `start` VARCHAR(45) NULL ,
  `end` VARCHAR(45) NULL ,
  `raw_file_id` INT NOT NULL ,
  `episode_id` INT NOT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_cutlist_raw_file` (`raw_file_id` ASC) ,
  INDEX `fk_cutlist_episode` (`episode_id` ASC) ,
  CONSTRAINT `fk_cutlist_raw_file`
    FOREIGN KEY (`raw_file_id` )
    REFERENCES `mydb`.`raw_file` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_cutlist_episode`
    FOREIGN KEY (`episode_id` )
    REFERENCES `mydb`.`episode` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'start and end times of clips, maybe a description';


-- -----------------------------------------------------
-- Table `mydb`.`state`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`state` ;

CREATE  TABLE IF NOT EXISTS `mydb`.`state` (
  `id` INT NOT NULL ,
  `slug` CHAR(10) NULL ,
  `sequence` INT NULL ,
  `description` VARCHAR(45) NULL ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`log`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`log` ;

CREATE  TABLE IF NOT EXISTS `mydb`.`log` (
  `id` INT NOT NULL ,
  `episode_id` INT NOT NULL ,
  `state_id` INT NOT NULL ,
  PRIMARY KEY (`id`, `state_id`) ,
  INDEX `fk_log_episode` (`episode_id` ASC) ,
  INDEX `fk_log_state` (`state_id` ASC) ,
  CONSTRAINT `fk_log_episode`
    FOREIGN KEY (`episode_id` )
    REFERENCES `mydb`.`episode` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_log_state`
    FOREIGN KEY (`state_id` )
    REFERENCES `mydb`.`state` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'log of processes appled (applying) to an event';


-- -----------------------------------------------------
-- Table `mydb`.`show`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`show` ;

CREATE  TABLE IF NOT EXISTS `mydb`.`show` (
  `id` INT NOT NULL ,
  `name` VARCHAR(45) NULL ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`season`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`season` ;

CREATE  TABLE IF NOT EXISTS `mydb`.`season` (
  `id` INT NOT NULL ,
  `show_id` INT NOT NULL ,
  `name` VARCHAR(45) NULL ,
  `episode_id` INT NOT NULL ,
  PRIMARY KEY (`id`, `episode_id`) ,
  INDEX `fk_season_show` (`show_id` ASC) ,
  INDEX `fk_season_episode` (`episode_id` ASC) ,
  CONSTRAINT `fk_season_show`
    FOREIGN KEY (`show_id` )
    REFERENCES `mydb`.`show` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_season_episode`
    FOREIGN KEY (`episode_id` )
    REFERENCES `mydb`.`episode` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;



SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
