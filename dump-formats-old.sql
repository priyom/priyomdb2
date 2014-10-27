
--
-- Dumping data for table `transmission_format_nodes`
--

LOCK TABLES `transmission_format_nodes` WRITE;
/*!40000 ALTER TABLE `transmission_format_nodes` DISABLE KEYS */;
INSERT INTO `transmission_format_nodes` VALUES (1,NULL,NULL,'1',0,NULL,NULL,NULL,0,'S28 style message'),(2,1,0,'+',0,NULL,' ','callwrap',1,'Group callsigns separated with space'),(3,1,1,'1',0,NULL,' ',NULL,0,'Single space'),(4,1,2,'+',0,NULL,' ','messagewrap',1,'Join message parts'),(5,2,0,'1',1,NULL,'[0-9]{2}\\s+[0-9]{3}','call',0,'“Callsign”'),(6,4,0,'1',0,NULL,NULL,NULL,0,'A single message'),(7,6,0,'1',1,NULL,'\\w+','codeword',0,'Single word'),(8,6,1,'1',0,NULL,' ',NULL,0,'Single space'),(9,6,2,'1',1,NULL,'([0-9]{2} ){3}[0-9]{2}','numbers',0,'Four two-digit numbers'),(10,NULL,NULL,'1',0,NULL,NULL,NULL,0,'3/4 digit ID + group count + 5 digit groups'),(11,10,0,'1',1,NULL,'[0-9?]{3,4}','id',0,'ID'),(12,10,1,'+',0,NULL,' ',NULL,0,'Space'),(13,10,2,'1',1,NULL,'[0-9?]{1,5}','group_count',0,'Group count'),(14,10,3,'+',0,NULL,' ',NULL,0,'Space'),(15,10,4,'1',0,NULL,' ','groupwrap',1,'Groups, joined with single space'),(16,15,0,'1',0,NULL,'[0-9?]{5}','group',0,'5 digit group'),(79,NULL,NULL,'1',0,NULL,NULL,NULL,0,'3/4 digit ID + group count + 5 digit groups'),(80,79,0,'1',1,NULL,'[0-9?]{3,4}','id',0,'ID'),(81,79,1,'+',0,NULL,' ',NULL,0,'Space'),(82,79,2,'1',1,NULL,'[0-9?]{1,5}','group_count',0,'Group count'),(83,79,3,'+',0,NULL,' ',NULL,0,'Space'),(84,79,4,'+',0,NULL,' ','groupwrap',1,'Groups, joined with single space'),(85,84,0,'1',0,NULL,'[0-9?]{5}','group',0,'5 digit group'),(90,NULL,NULL,'1',0,NULL,NULL,NULL,0,'3/4 digit ID + group count, without message'),(91,90,0,'1',1,NULL,'[0-9?]{3,4}','id',0,'ID'),(92,90,1,'+',0,NULL,' ',NULL,0,'Space'),(93,90,2,'1',1,NULL,'[0-9?]{1,5}','group_count',0,'Group count'),(104,NULL,NULL,'1',0,NULL,NULL,NULL,0,'4 figures'),(105,104,0,'*',0,NULL,' ','messagewrap',1,'messagewrap'),(106,105,0,'1',1,NULL,'[0-9?]{4}','group',0,'4 figure group'),(109,NULL,NULL,'+',0,NULL,' ',NULL,1,'5 figures'),(110,109,0,'+',0,NULL,' ','messagewrap',1,'messagewrap'),(111,110,0,'1',1,NULL,'[0-9?]{5}','group',0,'5 figure group'),(122,NULL,NULL,'1',0,NULL,NULL,NULL,0,'dlya groups of codeword + number'),(123,122,0,'+',0,NULL,' ','messagewrap',1,'messagewrap'),(124,123,0,'1',0,NULL,NULL,NULL,0,'dlya group of codeword + number'),(125,124,0,'1',1,NULL,'\\w+','codeword',0,'dlya codeword'),(126,124,1,'1',0,NULL,' ',NULL,0,'space'),(127,124,2,'1',1,NULL,'[0-9?]{2}','number',0,'dlya number');
/*!40000 ALTER TABLE `transmission_format_nodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `transmission_formats`
--

LOCK TABLES `transmission_formats` WRITE;
/*!40000 ALTER TABLE `transmission_formats` DISABLE KEYS */;
INSERT INTO `transmission_formats` VALUES ('2014-04-06 16:34:37','2014-04-06 16:34:37',1,'MDZhB (UZB-76) standard format','',1),('2014-04-06 16:45:00','2014-04-06 18:03:14',2,'3/4 digit ID + group count + 5 digit groups','Example: 123 4 12345 12345 12345 12345',79),('2014-04-06 17:54:42','2014-04-06 18:07:57',3,'3/4 digit ID + group count, without message','Example: 123 4',90),('2014-04-06 17:57:23','2014-04-06 18:35:39',4,'4 figure groups','Example: 1234 1234 1234',104),('2014-04-06 17:58:20','2014-04-06 18:40:31',5,'5 figure groups','Example: 12345 12345 12345',109),('2014-04-06 18:02:05','2014-04-06 18:45:11',6,'dlya groups of codeword + number','Example: FOO 12 BAR 34',122);
/*!40000 ALTER TABLE `transmission_formats` ENABLE KEYS */;
UNLOCK TABLES;
