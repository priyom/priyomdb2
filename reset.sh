#!/bin/bash
echo 'drop database priyom2; create database priyom2;' | mysql -u priyom2
mysql -u priyom2 priyom2 < dump-formats.sql
