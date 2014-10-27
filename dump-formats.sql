-- MySQL dump 10.14  Distrib 5.5.36-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: priyom2
-- ------------------------------------------------------
-- Server version	5.5.36-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

LOCK TABLES `transmission_format_nodes` WRITE;
/*!40000 ALTER TABLE `transmission_format_nodes` DISABLE KEYS */;
INSERT INTO `transmission_format_nodes` VALUES (10,NULL,NULL,'1',0,NULL,NULL,NULL,0,'3/4 digit ID + group count + 5 digit groups'),(11,10,0,'1',1,NULL,'[0-9?]{3,4}','id',0,'ID'),(12,10,1,'+',0,NULL,' ',NULL,0,'Space'),(13,10,2,'1',1,NULL,'[0-9?]{1,5}','group_count',0,'Group count'),(14,10,3,'+',0,NULL,' ',NULL,0,'Space'),(15,10,4,'1',0,NULL,' ','groupwrap',1,'Groups, joined with single space'),(16,15,0,'1',0,NULL,'[0-9?]{5}','group',0,'5 digit group'),(109,NULL,NULL,'+',0,NULL,' ',NULL,1,'5 figures'),(110,109,0,'+',0,NULL,' ','messagewrap',1,'messagewrap'),(111,110,0,'1',1,NULL,'[0-9?]{5}','group',0,'5 figure group'),(128,NULL,NULL,'1',0,NULL,NULL,NULL,0,'3/4 digit ID + group count + 5 digit groups'),(129,128,0,'1',1,NULL,'[0-9?]{3}','callsign',0,'Callsign'),(130,128,1,'+',0,NULL,' ',NULL,0,'Space'),(131,128,2,'1',1,NULL,'[0-9?]{3,4}','id',0,'ID'),(132,128,3,'+',0,NULL,' ',NULL,0,'Space'),(133,128,4,'1',1,NULL,'[0-9?]{1,5}','group_count',0,'Group count'),(134,128,5,'+',0,NULL,' ',NULL,0,'Space'),(135,128,6,'+',0,NULL,' ','groupwrap',1,'Groups, joined with single space'),(136,135,0,'1',0,NULL,'[0-9?]{5}','group',0,'5 digit group'),(143,NULL,NULL,'1',0,NULL,NULL,NULL,0,'3/4 digit ID + group count, without message'),(144,143,0,'1',1,NULL,'[0-9?]{3}','callsign',0,'Callsign'),(145,143,1,'+',0,NULL,' ',NULL,0,'Space'),(146,143,2,'1',1,NULL,'[0-9?]{3,4}','id',0,'ID'),(147,143,3,'+',0,NULL,' ',NULL,0,'Space'),(148,143,4,'1',1,NULL,'[0-9?]{1,5}','group_count',0,'Group count'),(149,NULL,NULL,'1',0,NULL,NULL,NULL,0,'4 figures'),(150,149,0,'1',1,NULL,'[0-9?]{3}','callsign',0,'Callsign'),(151,149,1,'1',0,NULL,' ',NULL,0,'Space'),(152,149,2,'*',0,NULL,' ','messagewrap',1,'messagewrap'),(153,152,0,'1',1,NULL,'[0-9?]{4}','group',0,'4 figure group'),(170,NULL,NULL,'1',0,NULL,NULL,NULL,0,'S28 style message'),(171,170,0,'+',0,NULL,' ','wrap_callsigns',1,'Callsign wrapper'),(172,170,1,'1',0,NULL,' ',NULL,0,'Space'),(173,170,2,'+',0,NULL,' ','wrap_root',1,'Root group (DD DDD (A+ DD DD DD DD)+)'),(174,171,0,'1',1,NULL,'[^/ ]+','callsign',0,'Callsign'),(175,173,0,'+',0,NULL,' ','wrap_callnumbers',1,'Callnumbers (DD DDD)'),(176,173,1,'1',0,NULL,' ',NULL,0,'Single space'),(177,173,2,'+',0,NULL,' ','wrap_message',1,'Message wrap (A+ DD DD DD DD)'),(178,175,0,'1',0,NULL,'[0-9?]{2}\\s+[0-9?]{3}','call',0,'Callnumber'),(179,177,0,'1',1,NULL,'[^/ ]+','message_word',0,'Single word'),(180,177,1,'1',0,NULL,' ',NULL,0,'Space'),(181,177,2,'1',1,NULL,'([0-9?]{2} ){3}[0-9?]{2}','message_digits',0,'Digits'),(190,NULL,NULL,'1',0,NULL,NULL,NULL,0,'dlya groups of codeword + number'),(191,190,0,'1',1,NULL,'[^/ ]+','callsign',0,'Callsign'),(192,190,1,'+',0,NULL,' ',NULL,0,'Space'),(193,190,2,'+',0,NULL,' ','messagewrap',1,'messagewrap'),(194,193,0,'1',0,NULL,NULL,NULL,0,'dlya group of codeword + number'),(195,194,0,'1',1,NULL,'[^/ ]+','codeword',0,'dlya codeword'),(196,194,1,'1',0,NULL,' ',NULL,0,'space'),(197,194,2,'1',1,NULL,'[0-9?]{2}','number',0,'dlya number'),(198,NULL,NULL,'1',0,NULL,NULL,NULL,0,'dlya groups of codeword + number'),(199,198,0,'+',0,NULL,' ','messagewrap',1,'messagewrap'),(200,199,0,'1',0,NULL,NULL,NULL,0,'dlya group of codeword + number'),(201,200,0,'1',1,NULL,'[^/ ]+','codeword',0,'dlya codeword');
/*!40000 ALTER TABLE `transmission_format_nodes` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `transmission_formats` WRITE;
/*!40000 ALTER TABLE `transmission_formats` DISABLE KEYS */;
INSERT INTO `transmission_formats` VALUES ('2014-04-06 16:34:37','2014-04-23 15:05:49',1,'MDZhB (UZB-76) standard format','',170),('2014-04-06 16:45:00','2014-04-23 15:00:53',2,'3 digit callsign + 3/4 digit ID + group count + 5 digit groups','Example: 123 123 4 12345 12345 12345 12345',128),('2014-04-06 17:54:42','2014-04-23 15:01:45',3,'3 digit callsign + 3/4 digit ID + group count, without message','Example: 123 123 4',143),('2014-04-06 17:57:23','2014-04-23 15:02:18',4,'3 digit callsign + 4 figure groups','Example: 123 1234 1234 1234',149),('2014-04-06 17:58:20','2014-04-06 18:40:31',5,'5 figure groups','Example: 12345 12345 12345',109),('2014-04-06 18:02:05','2014-04-23 15:11:37',6,'callsign + dlya groups of codeword + number','Example: FNORD FOO 12 BAR 34',190),('2014-04-23 15:02:36','2014-04-23 15:12:02',7,'dlya groups of codeword','Example: FOO BAR',198);
/*!40000 ALTER TABLE `transmission_formats` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2014-04-23 17:06:19
