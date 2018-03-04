-- MySQL dump 10.13  Distrib 5.7.21, for Linux (x86_64)
--
-- Host: localhost    Database: ncaa_bb
-- ------------------------------------------------------
-- Server version	5.7.21-0ubuntu0.16.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `basestats`
--

DROP TABLE IF EXISTS `basestats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `basestats` (
  `teamname` varchar(50) NOT NULL,
  `statdate` date NOT NULL,
  `points-per-game` float(7,4) DEFAULT NULL,
  `offensive-efficiency` float(7,4) DEFAULT NULL,
  `floor-percentage` float(7,4) DEFAULT NULL,
  `points-from-2-pointers` float(7,4) DEFAULT NULL,
  `points-from-3-pointers` float(7,4) DEFAULT NULL,
  `percent-of-points-from-2-pointers` float(7,4) DEFAULT NULL,
  `percent-of-points-from-3-pointers` float(7,4) DEFAULT NULL,
  `percent-of-points-from-free-throws` float(7,4) DEFAULT NULL,
  `defensive-efficiency` float(7,4) DEFAULT NULL,
  `shooting-pct` float(7,4) DEFAULT NULL,
  `fta-per-fga` float(7,4) DEFAULT NULL,
  `ftm-per-100-possessions` float(7,4) DEFAULT NULL,
  `free-throw-rate` float(7,4) DEFAULT NULL,
  `three-point-rate` float(7,4) DEFAULT NULL,
  `two-point-rate` float(7,4) DEFAULT NULL,
  `three-pointers-made-per-game` float(7,4) DEFAULT NULL,
  `effective-field-goal-pct` float(7,4) DEFAULT NULL,
  `true-shooting-percentage` float(7,4) DEFAULT NULL,
  `offensive-rebounds-per-game` float(7,4) DEFAULT NULL,
  `offensive-rebounding-pct` float(7,4) DEFAULT NULL,
  `defensive-rebounds-per-game` float(7,4) DEFAULT NULL,
  `defensive-rebounding-pct` float(7,4) DEFAULT NULL,
  `blocks-per-game` float(7,4) DEFAULT NULL,
  `steals-per-game` float(7,4) DEFAULT NULL,
  `block-pct` float(7,4) DEFAULT NULL,
  `steals-perpossession` float(7,4) DEFAULT NULL,
  `steal-pct` float(7,4) DEFAULT NULL,
  `assists-per-game` float(7,4) DEFAULT NULL,
  `turnovers-per-game` float(7,4) DEFAULT NULL,
  `turnovers-per-possession` float(7,4) DEFAULT NULL,
  `assist--per--turnover-ratio` float(7,4) DEFAULT NULL,
  `assists-per-fgm` float(7,4) DEFAULT NULL,
  `assists-per-possession` float(7,4) DEFAULT NULL,
  `turnover-pct` float(7,4) DEFAULT NULL,
  `personal-fouls-per-game` float(7,4) DEFAULT NULL,
  `personal-fouls-per-possession` float(7,4) DEFAULT NULL,
  `personal-foul-pct` float(7,4) DEFAULT NULL,
  `possessions-per-game` float(7,4) DEFAULT NULL,
  `extra-chances-per-game` float(7,4) DEFAULT NULL,
  `effective-possession-ratio` float(7,4) DEFAULT NULL,
  PRIMARY KEY (`teamname`,`statdate`),
  CONSTRAINT `fk_stat_teamname` FOREIGN KEY (`teamname`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `defensive_preds`
--

DROP TABLE IF EXISTS `defensive_preds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `defensive_preds` (
  `teamname` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `lightgbm_all` float(9,7) NOT NULL,
  `ridge_all` float(9,7) NOT NULL,
  `lasso_team` float(9,7) NOT NULL,
  `lightgbm_team` float(9,7) NOT NULL,
  `linsvm_team` float(9,7) NOT NULL,
  `ridge_team` float(9,7) NOT NULL,
  `lasso_possessions` float(9,7) NOT NULL,
  `lightgbm_possessions` float(9,7) NOT NULL,
  `ridge_possessions` float(9,7) NOT NULL,
  `lasso_target` float(9,7) NOT NULL,
  `lightgbm_target` float(9,7) NOT NULL,
  PRIMARY KEY (`teamname`,`date`),
  CONSTRAINT `fk_def_teamname` FOREIGN KEY (`teamname`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `future_games`
--

DROP TABLE IF EXISTS `future_games`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `future_games` (
  `oddsdate` date NOT NULL,
  `favorite` varchar(50) NOT NULL,
  `underdog` varchar(50) NOT NULL,
  `line` float(7,4) DEFAULT NULL,
  `juice` float(7,4) DEFAULT NULL,
  `overunder` float(7,4) DEFAULT NULL,
  `oujuice` float(7,4) DEFAULT NULL,
  `favmoneyline` float(7,2) DEFAULT NULL,
  `dogmoneyline` float(7,2) DEFAULT NULL,
  `favscore` int(11) DEFAULT NULL,
  `dogscore` int(11) DEFAULT NULL,
  `homeaway` int(11) DEFAULT NULL,
  PRIMARY KEY (`oddsdate`,`favorite`,`underdog`),
  KEY `fk_odds_favorite` (`favorite`),
  KEY `fk_odds_underdog` (`underdog`),
  CONSTRAINT `fk_future_favorite` FOREIGN KEY (`favorite`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_future_underdog` FOREIGN KEY (`underdog`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `gamedata`
--

DROP TABLE IF EXISTS `gamedata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gamedata` (
  `teamname` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `opponent` varchar(50) NOT NULL,
  `location` varchar(50) NOT NULL,
  PRIMARY KEY (`teamname`,`date`),
  CONSTRAINT `fk_team_teamname` FOREIGN KEY (`teamname`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `line_preds`
--

DROP TABLE IF EXISTS `line_preds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `line_preds` (
  `teamname` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `pca_line` float(9,7) NOT NULL,
  `tsvd_line` float(9,7) NOT NULL,
  `lasso_line` float(9,7) NOT NULL,
  `lightgbm_line` float(9,7) NOT NULL,
  `ridge_line` float(9,7) NOT NULL,
  PRIMARY KEY (`teamname`,`date`),
  CONSTRAINT `fk_line_teamname` FOREIGN KEY (`teamname`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `oddsdata`
--

DROP TABLE IF EXISTS `oddsdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oddsdata` (
  `oddsdate` date NOT NULL,
  `favorite` varchar(50) NOT NULL,
  `underdog` varchar(50) NOT NULL,
  `line` float(7,4) DEFAULT NULL,
  `juice` float(7,4) DEFAULT NULL,
  `overunder` float(7,4) DEFAULT NULL,
  `oujuice` float(7,4) DEFAULT NULL,
  `favmoneyline` float(7,2) DEFAULT NULL,
  `dogmoneyline` float(7,2) DEFAULT NULL,
  `favscore` int(11) DEFAULT NULL,
  `dogscore` int(11) DEFAULT NULL,
  `homeaway` int(11) DEFAULT NULL,
  PRIMARY KEY (`oddsdate`,`favorite`,`underdog`),
  KEY `fk_odds_favorite` (`favorite`),
  KEY `fk_odds_underdog` (`underdog`),
  CONSTRAINT `fk_odds_favorite` FOREIGN KEY (`favorite`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_odds_underdog` FOREIGN KEY (`underdog`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `offensive_preds`
--

DROP TABLE IF EXISTS `offensive_preds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `offensive_preds` (
  `teamname` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `lightgbm_team` float(9,7) NOT NULL,
  `linsvm_team` float(9,7) NOT NULL,
  `linsvm_all` float(9,7) NOT NULL,
  `ridge_all` float(9,7) NOT NULL,
  `lasso_possessions` float(9,7) NOT NULL,
  `lightgbm_possessions` float(9,7) NOT NULL,
  `linsvm_possessions` float(9,7) NOT NULL,
  `lightgbm_target` float(9,7) NOT NULL,
  `linsvm_target` float(9,7) NOT NULL,
  `ridge_target` float(9,7) NOT NULL,
  `lasso_target` float(9,7) NOT NULL,
  PRIMARY KEY (`teamname`,`date`),
  CONSTRAINT `fk_off_teamname` FOREIGN KEY (`teamname`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ou_preds`
--

DROP TABLE IF EXISTS `ou_preds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ou_preds` (
  `teamname` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `pca_ou` float(9,7) NOT NULL,
  `tsvd_ou` float(9,7) NOT NULL,
  `lasso_ou` float(9,7) NOT NULL,
  `lightgbm_ou` float(9,7) NOT NULL,
  `ridge_ou` float(9,7) NOT NULL,
  PRIMARY KEY (`teamname`,`date`),
  CONSTRAINT `fk_ou_teamname` FOREIGN KEY (`teamname`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rankings`
--

DROP TABLE IF EXISTS `rankings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rankings` (
  `teamname` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `defense_pace` float(9,7) NOT NULL,
  `defense_ppp` float(9,7) NOT NULL,
  `offense_pace` float(9,7) NOT NULL,
  `offense_ppp` float(9,7) NOT NULL,
  `+pts_share` float(9,7) NOT NULL,
  `keras_share` float(9,7) NOT NULL,
  PRIMARY KEY (`teamname`,`date`),
  CONSTRAINT `fk_rankings_teamname` FOREIGN KEY (`teamname`) REFERENCES `teamnames` (`teamname`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-03-03 19:43:46
