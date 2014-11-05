-- MySQL dump 10.14  Distrib 5.5.39-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: priyom2
-- ------------------------------------------------------
-- Server version	5.5.39-MariaDB

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
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('40c1cb72654');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alphabets`
--

DROP TABLE IF EXISTS `alphabets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alphabets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `short_name` varchar(10) NOT NULL,
  `display_name` varchar(127) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `short_name` (`short_name`),
  UNIQUE KEY `display_name` (`display_name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alphabets`
--

LOCK TABLES `alphabets` WRITE;
/*!40000 ALTER TABLE `alphabets` DISABLE KEYS */;
INSERT INTO `alphabets` VALUES (1,'la','Latin'),(2,'ru','Cyrillic');
/*!40000 ALTER TABLE `alphabets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attachments`
--

DROP TABLE IF EXISTS `attachments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `attachments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mime` varchar(63) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `attribution` varchar(127) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attachments`
--

LOCK TABLES `attachments` WRITE;
/*!40000 ALTER TABLE `attachments` DISABLE KEYS */;
/*!40000 ALTER TABLE `attachments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `capabilities`
--

DROP TABLE IF EXISTS `capabilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `capabilities` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(127) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `capabilities`
--

LOCK TABLES `capabilities` WRITE;
/*!40000 ALTER TABLE `capabilities` DISABLE KEYS */;
INSERT INTO `capabilities` VALUES (1,'view-station'),(2,'view-event'),(3,'log'),(4,'edit-self'),(5,'view-user'),(6,'view-alphabet'),(7,'view-format'),(8,'view-mode'),(9,'view-group'),(10,'log-unmoderated'),(11,'review-log'),(12,'create-alphabet'),(13,'edit-alphabet'),(14,'delete-alphabet'),(15,'create-mode'),(16,'edit-mode'),(17,'delete-mode'),(18,'view-group'),(19,'create-event'),(20,'view-event'),(21,'edit-event'),(22,'delete-event'),(23,'create-format'),(24,'view-format'),(25,'edit-format'),(26,'delete-format'),(27,'create-station'),(28,'view-station'),(29,'edit-station'),(30,'delete-station'),(31,'create-user'),(32,'view-user'),(33,'edit-user'),(34,'delete-user'),(35,'create-group'),(36,'view-group'),(37,'edit-group'),(38,'delete-group'),(39,'ROOT');
/*!40000 ALTER TABLE `capabilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `event_attachments`
--

DROP TABLE IF EXISTS `event_attachments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `event_attachments` (
  `attachment_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `relation` enum('recording','waterfall') DEFAULT NULL,
  PRIMARY KEY (`attachment_id`),
  KEY `event_id` (`event_id`),
  CONSTRAINT `event_attachments_ibfk_1` FOREIGN KEY (`attachment_id`) REFERENCES `attachments` (`id`),
  CONSTRAINT `event_attachments_ibfk_2` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `event_attachments`
--

LOCK TABLES `event_attachments` WRITE;
/*!40000 ALTER TABLE `event_attachments` DISABLE KEYS */;
/*!40000 ALTER TABLE `event_attachments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `event_classes`
--

DROP TABLE IF EXISTS `event_classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `event_classes` (
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `display_name` varchar(127) NOT NULL,
  `one_shot` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `event_classes`
--

LOCK TABLES `event_classes` WRITE;
/*!40000 ALTER TABLE `event_classes` DISABLE KEYS */;
/*!40000 ALTER TABLE `event_classes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `event_frequencies`
--

DROP TABLE IF EXISTS `event_frequencies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `event_frequencies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` int(11) NOT NULL,
  `frequency` bigint(20) NOT NULL,
  `mode_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `event_id` (`event_id`),
  KEY `mode_id` (`mode_id`),
  CONSTRAINT `event_frequencies_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`) ON DELETE CASCADE,
  CONSTRAINT `event_frequencies_ibfk_2` FOREIGN KEY (`mode_id`) REFERENCES `modes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `event_frequencies`
--

LOCK TABLES `event_frequencies` WRITE;
/*!40000 ALTER TABLE `event_frequencies` DISABLE KEYS */;
/*!40000 ALTER TABLE `event_frequencies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `events`
--

DROP TABLE IF EXISTS `events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `events` (
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `station_id` int(11) DEFAULT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT NULL,
  `event_class_id` int(11) DEFAULT NULL,
  `submitter_id` int(11) DEFAULT NULL,
  `approved` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `station_id` (`station_id`),
  KEY `event_class_id` (`event_class_id`),
  KEY `submitter_id` (`submitter_id`),
  CONSTRAINT `events_ibfk_1` FOREIGN KEY (`station_id`) REFERENCES `stations` (`id`),
  CONSTRAINT `events_ibfk_2` FOREIGN KEY (`event_class_id`) REFERENCES `event_classes` (`id`),
  CONSTRAINT `events_ibfk_3` FOREIGN KEY (`submitter_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `events`
--

LOCK TABLES `events` WRITE;
/*!40000 ALTER TABLE `events` DISABLE KEYS */;
/*!40000 ALTER TABLE `events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `format_node`
--

DROP TABLE IF EXISTS `format_node`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `format_node` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type_` varchar(4) DEFAULT NULL,
  `order` int(11) NOT NULL,
  `parent_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `format_node_fk_format_node_id` (`parent_id`),
  CONSTRAINT `format_node_fk_format_node_id` FOREIGN KEY (`parent_id`) REFERENCES `format_node` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=238 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `format_node`
--

LOCK TABLES `format_node` WRITE;
/*!40000 ALTER TABLE `format_node` DISABLE KEYS */;
INSERT INTO `format_node` VALUES (1,'srct',0,NULL),(2,'srct',0,1),(3,'sicn',0,1),(4,'srct',0,1),(5,'sicn',0,1),(6,'srct',0,1),(7,'sicn',0,2),(8,'sicn',0,4),(9,'sicn',0,4),(10,'sicn',0,4),(11,'srct',0,6),(12,'sicn',0,6),(13,'srct',0,6),(14,'sicn',0,11),(15,'srct',0,13),(16,'sicn',0,15),(17,'srct',0,NULL),(18,'srct',0,17),(19,'sicn',0,17),(20,'srct',0,17),(21,'sicn',0,17),(22,'srct',0,17),(23,'sicn',0,17),(24,'srct',0,17),(25,'sicn',0,18),(26,'sicn',0,20),(27,'sicn',0,22),(28,'sicn',0,24),(29,'srct',0,NULL),(30,'srct',0,29),(31,'sicn',0,29),(32,'srct',0,29),(33,'sicn',0,29),(34,'srct',0,29),(35,'sicn',0,29),(36,'srct',0,29),(37,'sicn',0,30),(38,'sicn',0,32),(39,'sicn',0,34),(40,'sicn',0,36),(41,'srct',0,NULL),(42,'srct',0,41),(43,'sicn',0,41),(44,'srct',0,41),(45,'sicn',0,41),(46,'srct',0,41),(47,'sicn',0,41),(48,'srct',0,41),(49,'sicn',0,42),(50,'sicn',0,44),(51,'sicn',0,46),(52,'sicn',0,48),(53,'srct',0,NULL),(54,'srct',0,53),(55,'sicn',0,54),(56,'srct',0,NULL),(57,'srct',0,56),(58,'srct',0,57),(59,'sicn',0,57),(60,'srct',0,57),(61,'sicn',0,58),(62,'sicn',0,60),(63,'srct',0,NULL),(64,'srct',0,NULL),(65,'srct',0,64),(66,'sicn',0,64),(67,'srct',0,64),(68,'sicn',0,64),(69,'srct',0,64),(70,'sicn',0,65),(71,'sicn',0,67),(72,'sicn',0,69),(73,'srct',0,NULL),(74,'srct',0,73),(75,'sicn',0,73),(76,'srct',0,73),(77,'sicn',0,73),(78,'srct',0,73),(79,'sicn',0,74),(80,'sicn',0,76),(81,'sicn',0,76),(82,'sicn',0,76),(83,'srct',0,78),(84,'sicn',0,78),(85,'srct',0,78),(86,'sicn',0,83),(87,'srct',0,85),(88,'sicn',0,87),(89,'srct',0,NULL),(90,'srct',0,89),(91,'sicn',0,89),(92,'srct',0,89),(93,'sicn',0,89),(94,'srct',0,89),(95,'sicn',0,90),(96,'sicn',0,92),(97,'sicn',0,92),(98,'sicn',0,92),(99,'srct',0,94),(100,'sicn',0,94),(101,'srct',0,94),(102,'sicn',0,99),(103,'srct',0,101),(104,'sicn',0,103),(121,'srct',0,NULL),(122,'srct',0,121),(123,'sicn',0,121),(124,'srct',0,121),(125,'sicn',0,121),(126,'srct',0,121),(127,'sicn',0,122),(128,'sicn',0,124),(129,'sicn',0,124),(130,'sicn',0,124),(131,'srct',0,126),(132,'sicn',0,126),(133,'srct',0,126),(134,'sicn',0,131),(135,'srct',0,133),(136,'sicn',0,135),(137,'srct',0,NULL),(138,'srct',0,137),(139,'sicn',0,137),(140,'sicn',0,137),(141,'sicn',0,137),(142,'srct',0,137),(143,'sicn',0,137),(144,'srct',0,137),(145,'sicn',0,138),(146,'sicn',0,142),(147,'srct',0,144),(148,'sicn',0,144),(149,'srct',0,144),(150,'sicn',0,144),(151,'srct',0,144),(152,'sicn',0,147),(153,'sicn',0,149),(154,'sicn',0,151),(155,'srct',0,NULL),(156,'srct',0,155),(157,'sicn',0,155),(158,'srct',0,155),(159,'sicn',0,155),(160,'srct',0,155),(161,'srct',0,156),(162,'sicn',0,158),(163,'sicn',0,158),(164,'sicn',0,158),(165,'srct',0,160),(166,'sicn',0,160),(167,'srct',0,160),(168,'sicn',0,161),(169,'sicn',0,165),(170,'srct',0,167),(171,'sicn',0,170),(172,'srct',0,NULL),(173,'srct',0,172),(174,'sicn',0,172),(175,'sicn',0,172),(176,'sicn',0,172),(177,'srct',0,172),(178,'sicn',0,172),(179,'srct',0,172),(180,'sicn',0,173),(181,'sicn',0,177),(182,'srct',0,179),(183,'sicn',0,179),(184,'srct',0,179),(185,'sicn',0,179),(186,'srct',0,179),(187,'sicn',0,182),(188,'sicn',0,184),(189,'sicn',0,186),(190,'srct',0,NULL),(191,'srct',0,190),(192,'sicn',0,190),(193,'sicn',0,190),(194,'sicn',0,190),(195,'srct',0,190),(196,'sicn',0,191),(197,'srct',0,195),(198,'sicn',0,195),(199,'srct',0,195),(200,'sicn',0,195),(201,'srct',0,195),(202,'sicn',0,197),(203,'sicn',0,199),(204,'sicn',0,201),(205,'srct',0,NULL),(206,'srct',0,205),(207,'sicn',0,205),(208,'sicn',0,205),(209,'sicn',0,205),(210,'srct',0,205),(211,'sicn',0,205),(212,'srct',0,205),(213,'sicn',0,206),(214,'sicn',0,210),(215,'srct',0,212),(216,'sicn',0,212),(217,'srct',0,212),(218,'sicn',0,212),(219,'srct',0,212),(220,'sicn',0,215),(221,'sicn',0,217),(222,'sicn',0,219),(223,'srct',0,NULL),(224,'srct',0,223),(225,'sicn',0,223),(226,'sicn',0,223),(227,'sicn',0,223),(228,'srct',0,223),(229,'sicn',0,224),(230,'srct',0,228),(231,'sicn',0,228),(232,'srct',0,228),(233,'sicn',0,228),(234,'srct',0,228),(235,'sicn',0,230),(236,'sicn',0,232),(237,'sicn',0,234);
/*!40000 ALTER TABLE `format_node` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `format_simple_content_node`
--

DROP TABLE IF EXISTS `format_simple_content_node`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `format_simple_content_node` (
  `id` int(11) NOT NULL,
  `kind` enum('digit','nonspace','alphabet_character','space','alphanumeric') NOT NULL,
  `nmin` int(11) NOT NULL,
  `nmax` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `format_structure_node_fk_format_node_id` FOREIGN KEY (`id`) REFERENCES `format_node` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `format_simple_content_node`
--

LOCK TABLES `format_simple_content_node` WRITE;
/*!40000 ALTER TABLE `format_simple_content_node` DISABLE KEYS */;
INSERT INTO `format_simple_content_node` VALUES (3,'space',1,NULL),(5,'space',1,NULL),(7,'alphanumeric',1,NULL),(8,'digit',2,2),(9,'space',1,NULL),(10,'digit',3,3),(12,'space',1,NULL),(14,'alphabet_character',1,NULL),(16,'digit',2,2),(19,'space',1,NULL),(21,'space',1,NULL),(23,'space',1,NULL),(25,'digit',3,3),(26,'digit',3,4),(27,'digit',1,5),(28,'digit',5,5),(31,'space',1,NULL),(33,'space',1,NULL),(35,'space',1,NULL),(37,'digit',3,3),(38,'digit',3,4),(39,'digit',1,5),(40,'digit',5,5),(43,'space',1,NULL),(45,'space',1,NULL),(47,'space',1,NULL),(49,'digit',3,3),(50,'digit',3,4),(51,'digit',1,5),(52,'digit',5,5),(55,'alphanumeric',1,NULL),(59,'space',1,NULL),(61,'alphanumeric',1,NULL),(62,'digit',2,2),(66,'space',1,NULL),(68,'space',1,NULL),(70,'digit',3,4),(71,'digit',1,5),(72,'digit',5,5),(75,'space',1,NULL),(77,'space',1,NULL),(79,'alphanumeric',1,NULL),(80,'digit',2,2),(81,'space',1,NULL),(82,'digit',3,3),(84,'space',1,NULL),(86,'alphabet_character',1,NULL),(88,'digit',2,2),(91,'space',1,NULL),(93,'space',1,NULL),(95,'alphanumeric',1,NULL),(96,'digit',2,2),(97,'space',1,NULL),(98,'digit',3,3),(100,'space',1,NULL),(102,'alphabet_character',1,NULL),(104,'digit',2,2),(123,'space',1,NULL),(125,'space',1,NULL),(127,'alphanumeric',1,NULL),(128,'digit',2,2),(129,'space',1,NULL),(130,'digit',3,3),(132,'space',1,NULL),(134,'alphabet_character',1,NULL),(136,'digit',2,2),(139,'space',1,NULL),(140,'digit',1,NULL),(141,'space',1,NULL),(143,'space',1,NULL),(145,'digit',3,3),(146,'digit',5,5),(148,'space',1,NULL),(150,'space',1,NULL),(152,'digit',3,3),(153,'digit',1,NULL),(154,'digit',5,5),(157,'space',1,NULL),(159,'space',1,NULL),(162,'digit',2,2),(163,'space',1,NULL),(164,'digit',3,3),(166,'space',1,NULL),(168,'alphanumeric',1,NULL),(169,'alphabet_character',1,NULL),(171,'digit',2,2),(174,'space',1,NULL),(175,'digit',1,NULL),(176,'space',1,NULL),(178,'space',1,NULL),(180,'digit',3,3),(181,'digit',5,5),(183,'space',1,NULL),(185,'space',1,NULL),(187,'digit',3,3),(188,'digit',1,NULL),(189,'digit',5,5),(192,'space',1,NULL),(193,'digit',1,NULL),(194,'space',1,NULL),(196,'digit',3,3),(198,'space',1,NULL),(200,'space',1,NULL),(202,'digit',3,3),(203,'digit',1,NULL),(204,'digit',5,5),(207,'space',1,NULL),(208,'digit',1,NULL),(209,'space',1,NULL),(211,'space',1,NULL),(213,'digit',3,3),(214,'digit',5,5),(216,'space',1,NULL),(218,'space',1,NULL),(220,'digit',3,4),(221,'digit',1,NULL),(222,'digit',5,5),(225,'space',1,NULL),(226,'digit',1,NULL),(227,'space',1,NULL),(229,'digit',3,3),(231,'space',1,NULL),(233,'space',1,NULL),(235,'digit',3,4),(236,'digit',1,NULL),(237,'digit',5,5);
/*!40000 ALTER TABLE `format_simple_content_node` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `format_structure_node`
--

DROP TABLE IF EXISTS `format_structure_node`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `format_structure_node` (
  `id` int(11) NOT NULL,
  `joiner_regex` varchar(255) DEFAULT NULL,
  `joiner_const` varchar(255) DEFAULT NULL,
  `save_to` varchar(255) DEFAULT NULL,
  `nmin` int(11) NOT NULL,
  `nmax` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `format_structure_fk_format_node_id` FOREIGN KEY (`id`) REFERENCES `format_node` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `format_structure_node`
--

LOCK TABLES `format_structure_node` WRITE;
/*!40000 ALTER TABLE `format_structure_node` DISABLE KEYS */;
INSERT INTO `format_structure_node` VALUES (1,NULL,NULL,NULL,1,1),(2,NULL,NULL,'callsign',1,1),(4,'\\s+',' ','call',1,NULL),(6,'\\s+',' ',NULL,1,NULL),(11,NULL,NULL,'codeword',1,1),(13,NULL,NULL,'numbers',1,1),(15,'\\s+',' ',NULL,4,4),(17,NULL,NULL,NULL,1,1),(18,NULL,NULL,'callsign',1,1),(20,NULL,NULL,'id',1,1),(22,NULL,NULL,'group_count',1,1),(24,'\\s+',' ','group',1,NULL),(29,NULL,NULL,NULL,1,1),(30,NULL,NULL,'callsign',1,1),(32,NULL,NULL,'id',1,1),(34,NULL,NULL,'group_count',1,1),(36,'\\s+',' ','group',0,NULL),(41,NULL,NULL,NULL,1,1),(42,NULL,NULL,'callsign',1,1),(44,NULL,NULL,'id',1,1),(46,NULL,NULL,'group_count',1,1),(48,'\\s+',' ','group',0,NULL),(53,NULL,NULL,NULL,1,1),(54,'\\s+',' ','codeword',1,NULL),(56,NULL,NULL,NULL,1,1),(57,'\\s+',' ',NULL,1,NULL),(58,NULL,NULL,'codeword',1,1),(60,NULL,NULL,'number',1,1),(63,NULL,NULL,NULL,1,1),(64,NULL,NULL,NULL,1,1),(65,NULL,NULL,'id',1,1),(67,NULL,NULL,'group_count',1,1),(69,'\\s+',' ','group',0,NULL),(73,NULL,NULL,NULL,1,1),(74,NULL,NULL,'callsign',1,1),(76,'\\s+',' ','call',1,NULL),(78,'\\s+',' ',NULL,1,NULL),(83,NULL,NULL,'codeword',1,1),(85,NULL,NULL,'numbers',1,1),(87,'\\s+',' ',NULL,4,4),(89,NULL,NULL,NULL,1,1),(90,NULL,NULL,'callsign',1,1),(92,'\\s+',' ','call',1,NULL),(94,'\\s+',' ',NULL,1,NULL),(99,NULL,NULL,'codeword',1,1),(101,NULL,NULL,'numbers',1,1),(103,'\\s+',' ',NULL,2,2),(121,NULL,NULL,NULL,1,1),(122,NULL,NULL,'callsign',1,1),(124,'\\s+',' ','call',1,NULL),(126,'\\s+',' ',NULL,1,NULL),(131,NULL,NULL,'codeword',1,1),(133,NULL,NULL,'numbers',1,1),(135,'\\s+',' ',NULL,2,2),(137,NULL,NULL,NULL,1,1),(138,NULL,NULL,'transmission_id',1,1),(142,NULL,NULL,'prefix_number',1,1),(144,NULL,NULL,NULL,1,1),(147,NULL,NULL,'call',1,1),(149,NULL,NULL,'group_count',1,1),(151,'\\s+',' ','number',1,NULL),(155,NULL,NULL,NULL,1,1),(156,NULL,NULL,'callsign',1,1),(158,'\\s+',' ','call',1,NULL),(160,'\\s+',' ',NULL,1,NULL),(161,'\\s+',' ',NULL,1,NULL),(165,NULL,NULL,'codeword',1,1),(167,NULL,NULL,'numbers',1,1),(170,'\\s+',' ',NULL,4,4),(172,NULL,NULL,NULL,1,1),(173,NULL,NULL,'transmission_id',1,1),(177,NULL,NULL,'prefix_number',1,1),(179,'\\s+',' ',NULL,1,NULL),(182,NULL,NULL,'call',1,1),(184,NULL,NULL,'group_count',1,1),(186,'\\s+',' ','number',1,NULL),(190,NULL,NULL,NULL,1,1),(191,NULL,NULL,'transmission_id',1,1),(195,'\\s+',' ',NULL,1,NULL),(197,NULL,NULL,'call',1,1),(199,NULL,NULL,'group_count',1,1),(201,'\\s+',' ','number',1,NULL),(205,NULL,NULL,NULL,1,1),(206,NULL,NULL,'transmission_id',1,1),(210,NULL,NULL,'prefix_number',1,1),(212,'\\s+',' ',NULL,1,NULL),(215,NULL,NULL,'call',1,1),(217,NULL,NULL,'group_count',1,1),(219,'\\s+',' ','number',1,NULL),(223,NULL,NULL,NULL,1,1),(224,NULL,NULL,'transmission_id',1,1),(228,'\\s+',' ',NULL,1,NULL),(230,NULL,NULL,'call',1,1),(232,NULL,NULL,'group_count',1,1),(234,'\\s+',' ','number',1,NULL);
/*!40000 ALTER TABLE `format_structure_node` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formats`
--

DROP TABLE IF EXISTS `formats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `formats` (
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `display_name` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `root_node_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `formats_fk_format_structure_node_id` (`root_node_id`),
  CONSTRAINT `formats_fk_format_structure_node_id` FOREIGN KEY (`root_node_id`) REFERENCES `format_structure_node` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formats`
--

LOCK TABLES `formats` WRITE;
/*!40000 ALTER TABLE `formats` DISABLE KEYS */;
INSERT INTO `formats` VALUES ('2014-11-05 15:24:37','2014-11-06 13:01:30',1,'Monolyth (4 number groups)','',155),('2014-11-05 15:27:15','2014-11-05 15:27:47',2,'3 digit callsign, 3â€“4 digit id, group count, arbitrary amount of 5 digit groups (may be none)','',41),('2014-11-05 15:30:13','2014-11-05 15:30:13',3,'Dlya (without numbers)','',53),('2014-11-05 15:31:01','2014-11-05 15:31:01',4,'Dlya (with umbers)','',56),('2014-11-05 15:32:37','2014-11-05 15:32:37',5,'The empty message','',63),('2014-11-05 15:41:42','2014-11-05 15:41:42',6,'3â€“4 digit id, group count, arbitrary amount of 5 digit groups (may be none)','',64),('2014-11-05 18:27:27','2014-11-05 18:28:44',7,'Monolyth (2 number groups)','',121),('2014-11-06 12:56:40','2014-11-06 13:53:17',8,'E07a format','',205),('2014-11-06 13:05:11','2014-11-06 13:53:27',9,'E07 format','',223);
/*!40000 ALTER TABLE `formats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_capabilities`
--

DROP TABLE IF EXISTS `group_capabilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `group_capabilities` (
  `capability_id` int(11) DEFAULT NULL,
  `group_id` int(11) DEFAULT NULL,
  KEY `capability_id` (`capability_id`),
  KEY `group_id` (`group_id`),
  CONSTRAINT `group_capabilities_ibfk_1` FOREIGN KEY (`capability_id`) REFERENCES `capabilities` (`id`),
  CONSTRAINT `group_capabilities_ibfk_2` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_capabilities`
--

LOCK TABLES `group_capabilities` WRITE;
/*!40000 ALTER TABLE `group_capabilities` DISABLE KEYS */;
INSERT INTO `group_capabilities` VALUES (39,2),(1,1),(2,1),(19,3),(20,3),(21,3),(22,3),(23,3),(24,3),(25,3),(26,3),(27,3),(28,3),(29,3),(30,3),(31,3),(32,3),(33,3),(34,3),(35,3),(36,3),(37,3),(38,3),(11,4),(12,4),(13,4),(14,4),(15,4),(16,4),(17,4),(18,4),(10,6),(3,5),(7,5),(5,5),(6,5),(8,5),(9,5),(4,5);
/*!40000 ALTER TABLE `group_capabilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(127) NOT NULL,
  `supergroup_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `groups_fk_supergroup_id` (`supergroup_id`),
  CONSTRAINT `groups_fk_supergroup_id` FOREIGN KEY (`supergroup_id`) REFERENCES `groups` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `groups`
--

LOCK TABLES `groups` WRITE;
/*!40000 ALTER TABLE `groups` DISABLE KEYS */;
INSERT INTO `groups` VALUES (1,'anonymous',NULL),(2,'wheel',NULL),(3,'admins',2),(4,'moderators',3),(5,'registered',4),(6,'unmoderated',4);
/*!40000 ALTER TABLE `groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `modes`
--

DROP TABLE IF EXISTS `modes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `modes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `display_name` varchar(63) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `display_name` (`display_name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `modes`
--

LOCK TABLES `modes` WRITE;
/*!40000 ALTER TABLE `modes` DISABLE KEYS */;
/*!40000 ALTER TABLE `modes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stations`
--

DROP TABLE IF EXISTS `stations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stations` (
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enigma_id` varchar(23) NOT NULL,
  `priyom_id` varchar(23) NOT NULL,
  `nickname` varchar(127) DEFAULT NULL,
  `description` text,
  `status` varchar(255) DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `enigma_id` (`enigma_id`,`priyom_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stations`
--

LOCK TABLES `stations` WRITE;
/*!40000 ALTER TABLE `stations` DISABLE KEYS */;
/*!40000 ALTER TABLE `stations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transmission_content_nodes`
--

DROP TABLE IF EXISTS `transmission_content_nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmission_content_nodes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_id` int(11) NOT NULL,
  `format_node_id` int(11) NOT NULL,
  `order` int(11) NOT NULL,
  `child_number` int(11) NOT NULL,
  `segment` varchar(127) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `content_id` (`content_id`),
  KEY `format_node_id` (`format_node_id`),
  CONSTRAINT `transmission_content_nodes_ibfk_1` FOREIGN KEY (`content_id`) REFERENCES `transmission_structured_contents` (`id`) ON DELETE CASCADE,
  CONSTRAINT `transmission_content_nodes_ibfk_2` FOREIGN KEY (`format_node_id`) REFERENCES `format_node` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transmission_content_nodes`
--

LOCK TABLES `transmission_content_nodes` WRITE;
/*!40000 ALTER TABLE `transmission_content_nodes` DISABLE KEYS */;
/*!40000 ALTER TABLE `transmission_content_nodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transmission_contents`
--

DROP TABLE IF EXISTS `transmission_contents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmission_contents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` int(11) NOT NULL,
  `mime` varchar(127) NOT NULL,
  `is_transcribed` tinyint(1) NOT NULL,
  `is_transcoded` tinyint(1) NOT NULL,
  `alphabet_id` int(11) DEFAULT NULL,
  `attribution` varchar(255) DEFAULT NULL,
  `subtype` varchar(50) NOT NULL,
  `parent_contents_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `event_id` (`event_id`),
  KEY `alphabet_id` (`alphabet_id`),
  KEY `parent_contents_id` (`parent_contents_id`),
  CONSTRAINT `transmission_contents_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`) ON DELETE CASCADE,
  CONSTRAINT `transmission_contents_ibfk_2` FOREIGN KEY (`alphabet_id`) REFERENCES `alphabets` (`id`),
  CONSTRAINT `transmission_contents_ibfk_3` FOREIGN KEY (`parent_contents_id`) REFERENCES `transmission_contents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transmission_contents`
--

LOCK TABLES `transmission_contents` WRITE;
/*!40000 ALTER TABLE `transmission_contents` DISABLE KEYS */;
/*!40000 ALTER TABLE `transmission_contents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transmission_raw_contents`
--

DROP TABLE IF EXISTS `transmission_raw_contents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmission_raw_contents` (
  `id` int(11) NOT NULL,
  `encoding` varchar(63) NOT NULL,
  `contents` blob,
  PRIMARY KEY (`id`),
  CONSTRAINT `transmission_raw_contents_ibfk_1` FOREIGN KEY (`id`) REFERENCES `transmission_contents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transmission_raw_contents`
--

LOCK TABLES `transmission_raw_contents` WRITE;
/*!40000 ALTER TABLE `transmission_raw_contents` DISABLE KEYS */;
/*!40000 ALTER TABLE `transmission_raw_contents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transmission_structured_contents`
--

DROP TABLE IF EXISTS `transmission_structured_contents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmission_structured_contents` (
  `id` int(11) NOT NULL,
  `format_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `format_id` (`format_id`),
  CONSTRAINT `transmission_structured_contents_ibfk_1` FOREIGN KEY (`id`) REFERENCES `transmission_contents` (`id`) ON DELETE CASCADE,
  CONSTRAINT `transmission_structured_contents_ibfk_2` FOREIGN KEY (`format_id`) REFERENCES `formats` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transmission_structured_contents`
--

LOCK TABLES `transmission_structured_contents` WRITE;
/*!40000 ALTER TABLE `transmission_structured_contents` DISABLE KEYS */;
/*!40000 ALTER TABLE `transmission_structured_contents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_groups`
--

DROP TABLE IF EXISTS `user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_groups` (
  `group_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  KEY `group_id` (`group_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `user_groups_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  CONSTRAINT `user_groups_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_groups`
--

LOCK TABLES `user_groups` WRITE;
/*!40000 ALTER TABLE `user_groups` DISABLE KEYS */;
INSERT INTO `user_groups` VALUES (2,1),(3,1),(4,1),(5,1),(6,1);
/*!40000 ALTER TABLE `user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_sessions`
--

DROP TABLE IF EXISTS `user_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_sessions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_key` binary(127) NOT NULL,
  `user_id` int(11) NOT NULL,
  `expiration` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `session_key` (`session_key`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `user_sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_sessions`
--

LOCK TABLES `user_sessions` WRITE;
/*!40000 ALTER TABLE `user_sessions` DISABLE KEYS */;
INSERT INTO `user_sessions` VALUES (1,'~‘š Ö™&ó©$³£^j¼¯\nÁCÒ‰=¦ç°­\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0',1,'2014-11-12 15:24:06');
/*!40000 ALTER TABLE `user_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `loginname` varchar(63) NOT NULL,
  `loginname_displayed` varchar(63) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_verifier` blob NOT NULL,
  `timezone` varchar(127) NOT NULL DEFAULT 'Etc/UTC',
  `locale` varchar(31) NOT NULL DEFAULT 'en_GB',
  PRIMARY KEY (`id`),
  UNIQUE KEY `loginname` (`loginname`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('2014-11-05 15:11:54','2014-11-05 15:24:06',1,'root','root','root@api.priyom.org','sha256$16384$ut/JdWCCOtb+6YDBn0xD+aXH$F9BNt7Vy0OsQBQyyMSPQAt1/IXeldUdu+VNXkSmAbDY=','Etc/UTC','en_GB');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2014-11-06 14:53:31
