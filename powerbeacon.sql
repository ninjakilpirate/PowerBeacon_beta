-- MySQL dump 10.17  Distrib 10.3.22-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: powerbeacon
-- ------------------------------------------------------
-- Server version	10.3.22-MariaDB-1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `checkins`
--

DROP TABLE IF EXISTS `checkins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `checkins` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `UUID` varchar(50) DEFAULT NULL,
  `gateway` varchar(30) DEFAULT NULL,
  `last_checkin` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `UUID` (`UUID`),
  CONSTRAINT `checkins_ibfk_1` FOREIGN KEY (`UUID`) REFERENCES `implants` (`UUID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=71 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `checkins`
--

LOCK TABLES `checkins` WRITE;
/*!40000 ALTER TABLE `checkins` DISABLE KEYS */;
INSERT INTO `checkins` VALUES (61,'TEST','1.2.3.4','2021-12-05 03:46:32'),(62,'TEST','1.2.3.4','2021-12-05 03:46:33'),(63,'TEST','1.2.3.4','2021-12-05 03:46:34'),(64,'TEST','1.2.3.4','2021-12-05 03:46:35'),(65,'TEST','5.6.7.8','2021-12-05 03:46:41'),(66,'TEST2','9.8.6.5','2021-12-05 03:47:13'),(67,'TEST','192.168.21.1','2021-12-05 04:12:45'),(68,'TEST','192.168.21.1','2021-12-05 04:13:00'),(69,'TEST2','192.168.21.1','2021-12-05 04:13:15'),(70,'TEST2','192.168.21.1','2021-12-05 04:13:30');
/*!40000 ALTER TABLE `checkins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `datastore`
--

DROP TABLE IF EXISTS `datastore`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `datastore` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `UUID` varchar(50) DEFAULT NULL,
  `delivered` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data` longtext DEFAULT NULL,
  `details` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `UUID` (`UUID`),
  CONSTRAINT `datastore_ibfk_1` FOREIGN KEY (`UUID`) REFERENCES `implants` (`UUID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `datastore`
--

LOCK TABLES `datastore` WRITE;
/*!40000 ALTER TABLE `datastore` DISABLE KEYS */;
/*!40000 ALTER TABLE `datastore` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `implants`
--

DROP TABLE IF EXISTS `implants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `implants` (
  `UUID` varchar(50) NOT NULL,
  `implantkey` varchar(50) DEFAULT NULL,
  `notes` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`UUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `implants`
--

LOCK TABLES `implants` WRITE;
/*!40000 ALTER TABLE `implants` DISABLE KEYS */;
INSERT INTO `implants` VALUES ('TEST','12345','none'),('TEST2','12345','none');
/*!40000 ALTER TABLE `implants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tasks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task` varchar(8000) DEFAULT NULL,
  `time_complete` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `done` tinyint(1) NOT NULL DEFAULT 0,
  `UUID` varchar(100) DEFAULT NULL,
  `is_complete` tinyint(1) DEFAULT 0,
  `notes` varchar(2500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `UUID` (`UUID`),
  CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`UUID`) REFERENCES `implants` (`UUID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=219 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tasks`
--

LOCK TABLES `tasks` WRITE;
/*!40000 ALTER TABLE `tasks` DISABLE KEYS */;
/*!40000 ALTER TABLE `tasks` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-12-05  4:35:29
