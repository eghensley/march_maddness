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
-- Table structure for table `teamnames`
--

DROP TABLE IF EXISTS `teamnames`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `teamnames` (
  `teamname` varchar(50) NOT NULL,
  PRIMARY KEY (`teamname`),
  UNIQUE KEY `teamname_UNIQUE` (`teamname`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teamnames`
--

LOCK TABLES `teamnames` WRITE;
/*!40000 ALTER TABLE `teamnames` DISABLE KEYS */;
INSERT INTO `teamnames` VALUES ('Abilene Christian'),('Air Force'),('Akron'),('Alab A&M'),('Alabama'),('Alabama St'),('Albany'),('Alcorn State'),('American'),('App State'),('AR Lit Rock'),('Arizona'),('Arizona St'),('Ark Pine Bl'),('Arkansas'),('Arkansas St'),('Army'),('Auburn'),('Austin Peay'),('Ball State'),('Baylor'),('Belmont'),('Beth-Cook'),('Binghamton'),('Boise State'),('Boston Col'),('Boston U'),('Bowling Grn'),('Bradley'),('Brown'),('Bryant'),('Bucknell'),('Buffalo'),('Butler'),('BYU'),('Cal Poly'),('Cal St Nrdge'),('California'),('Campbell'),('Canisius'),('Central Ark'),('Central Conn'),('Central FL'),('Central Mich'),('Charl South'),('Charlotte'),('Chattanooga'),('Chicago St'),('Cincinnati'),('Citadel'),('Clemson'),('Cleveland St'),('Coastal Car'),('Col Charlestn'),('Colgate'),('Colorado'),('Colorado St'),('Columbia'),('Connecticut'),('Coppin State'),('Cornell'),('Creighton'),('CS Bakersfld'),('CS Fullerton'),('Dartmouth'),('Davidson'),('Dayton'),('Delaware'),('Delaware St'),('Denver'),('DePaul'),('Detroit'),('Drake'),('Drexel'),('Duke'),('Duquesne'),('E Carolina'),('E Illinois'),('E Kentucky'),('E Michigan'),('E Tenn St'),('E Washingtn'),('Elon'),('Evansville'),('F Dickinson'),('Fairfield'),('Fla Atlantic'),('Fla Gulf Cst'),('Florida'),('Florida A&M'),('Florida Intl'),('Florida St'),('Fordham'),('Fresno St'),('Furman'),('GA Southern'),('GA Tech'),('Gard-Webb'),('Geo Mason'),('Geo Wshgtn'),('Georgetown'),('Georgia'),('Georgia St'),('Gonzaga'),('Grambling St'),('Grand Canyon'),('Hampton'),('Hartford'),('Harvard'),('Hawaii'),('High Point'),('Hofstra'),('Holy Cross'),('Houston'),('Houston Bap'),('Howard'),('Idaho'),('Idaho State'),('IL-Chicago'),('Illinois'),('Illinois St'),('Incarnate Word'),('Indiana'),('Indiana St'),('Iona'),('Iowa'),('Iowa State'),('IPFW'),('IUPUI'),('Jackson St'),('Jacksonville'),('James Mad'),('Jksnville St'),('Kansas'),('Kansas St'),('Kennesaw St'),('Kent State'),('Kentucky'),('LA Lafayette'),('LA Monroe'),('La Salle'),('LA Tech'),('Lafayette'),('Lamar'),('Lehigh'),('Lg Beach St'),('Liberty'),('Lipscomb'),('LIU-Brooklyn'),('Longwood'),('Louisville'),('Loyola Mymt'),('Loyola-Chi'),('Loyola-MD'),('LSU'),('Maine'),('Manhattan'),('Marist'),('Marquette'),('Marshall'),('Maryland'),('Maryland BC'),('Maryland ES'),('Mass Lowell'),('McNeese St'),('Memphis'),('Mercer'),('Miami (FL)'),('Miami (OH)'),('Michigan'),('Michigan St'),('Middle Tenn'),('Minnesota'),('Miss State'),('Miss Val St'),('Mississippi'),('Missouri'),('Missouri St'),('Monmouth'),('Montana'),('Montana St'),('Morehead St'),('Morgan St'),('Mt St Marys'),('Murray St'),('N Arizona'),('N Carolina'),('N Colorado'),('N Dakota St'),('N Florida'),('N Hampshire'),('N Illinois'),('N Iowa'),('N Kentucky'),('N Mex State'),('Navy'),('NC A&T'),('NC Central'),('NC State'),('NC-Asheville'),('NC-Grnsboro'),('NC-Wilmgton'),('Neb Omaha'),('Nebraska'),('Nevada'),('New Mexico'),('New Orleans'),('Niagara'),('Nicholls St'),('NJIT'),('Norfolk St'),('North Dakota'),('North Texas'),('Northeastrn'),('Northwestern'),('Notre Dame'),('NW State'),('Oakland'),('Ohio'),('Ohio State'),('Oklahoma'),('Oklahoma St'),('Old Dominion'),('Oral Roberts'),('Oregon'),('Oregon St'),('Pacific'),('Penn State'),('Pepperdine'),('Pittsburgh'),('Portland'),('Portland St'),('Prairie View'),('Presbyterian'),('Princeton'),('Providence'),('Purdue'),('Quinnipiac'),('Radford'),('Rhode Island'),('Rice'),('Richmond'),('Rider'),('Rob Morris'),('Rutgers'),('S Alabama'),('S Car State'),('S Carolina'),('S Dakota St'),('S Florida'),('S Illinois'),('S Methodist'),('S Mississippi'),('S Utah'),('Sac State'),('Sacred Hrt'),('Saint Louis'),('Sam Hous St'),('Samford'),('San Diego'),('San Diego St'),('San Fransco'),('San Jose St'),('Santa Clara'),('Savannah St'),('SC Upstate'),('SE Louisiana'),('SE Missouri'),('Seattle'),('Seton Hall'),('Siena'),('SIU Edward'),('South Dakota'),('Southern'),('St Bonavent'),('St Fran (NY)'),('St Fran (PA)'),('St Johns'),('St Josephs'),('St Marys'),('St Peters'),('Stanford'),('Ste F Austin'),('Stetson'),('Stony Brook'),('Syracuse'),('Temple'),('Tennessee'),('Texas'),('Texas A&M'),('Texas State'),('Texas Tech'),('TN Martin'),('TN State'),('TN Tech'),('Toledo'),('Towson'),('Troy'),('Tulane'),('Tulsa'),('TX A&M-CC'),('TX Christian'),('TX El Paso'),('TX Southern'),('TX-Arlington'),('TX-Pan Am'),('TX-San Ant'),('U Mass'),('U Penn'),('UAB'),('UC Davis'),('UC Irvine'),('UC Riverside'),('UCLA'),('UCSB'),('UMKC'),('UNLV'),('USC'),('Utah'),('Utah State'),('Utah Val St'),('VA Military'),('VA Tech'),('Valparaiso'),('Vanderbilt'),('VCU'),('Vermont'),('Villanova'),('Virginia'),('W Carolina'),('W Illinois'),('W Kentucky'),('W Michigan'),('W Virginia'),('Wagner'),('Wake Forest'),('Wash State'),('Washington'),('Weber State'),('WI-Grn Bay'),('WI-Milwkee'),('Wichita St'),('Winthrop'),('Wisconsin'),('Wm & Mary'),('Wofford'),('Wright State'),('Wyoming'),('Xavier'),('Yale'),('Youngs St');
/*!40000 ALTER TABLE `teamnames` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-03-03 19:44:03
