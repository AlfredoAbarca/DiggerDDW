#!/bin/python
#==========================================================
#
# Description: 
# Script to collect and normalize information regarding Dark Web sites
# based on certain search terms, using Onion Search tool as information collector
# and Neo4j as database engine. 
# Author: Alfredo Abarca (@aabarcab)
# Date: July 2023
# Languaje: Python V3
# 
#==========================================================

import os
import datetime
from neo4j import GraphDatabase
from langdetect import detect

#Global Variables
Words_File_Name="Words_To_Search.lst"
Tags_File_Name="Tags.lst"
Date=datetime.datetime.now()
IndexTime=Date.strftime("%Y-%m-%d")
Normalized_File_Name="All_Sites_" + Date.strftime("%d%m%y") + ".csv"
Cmd_Line=""
DB_Username="xxxxxx"
DB_Password="xxxxxx"
DB_URI="neo4j://xxx.xxx.xxx.xxx:7687"
DB_Driver=""
Register_Fields=9

#Function Definitions
def Get_tag_list(text_to_check,tags_file):
	tag_list=[]
	f=open(tags_file,'r')
	for line in f:
		if not line.startswith('#') and not line.startswith('\n'):
			splitted_line=line.split(':')
			keywords=splitted_line[1].split(',')
			if len(keywords[0])>0:
				for word in keywords:
					if word in text_to_check:
						tag_list.append(splitted_line[0].replace('\n',''))
						break;
	f.close()
	tags_set=set(tag_list)
	tags_list=(list(tags_set))
	return tags_list

def Normalize_Whole_Results(AllHostsFileName):
	outputFile="New_" + AllHostsFileName
	f_out=open(outputFile,'w')
	f_in=open(AllHostsFileName,'r')
	for line in f_in:
		split_line=line.split(';')
		Description=split_line[1]
		Domain=split_line[3]
		if len(Domain)>0:
			tags=[]
			tags=Get_tag_list(Description,Tags_File_Name)
			tag_separator=':'
			tags=tag_separator.join(tags)
			#translator=Translator()
			try:	
				transR=detect(Description)
			except Exception as e:
				transR='NI'
			if len(Domain)<60:
				version=2
			else:
				version=3

			New_Row=line.replace('\n','') + ';' + tags + ';' + transR + ';' + IndexTime + ';' + str(version) + '\n'
			print(New_Row)
			f_out.write(New_Row)
	f_out.close()
	f_in.close()

			
def Insert_Into_Log4J(Normalized_File):
	print("Inserting Records")
	f=open(Normalized_File,'r')
	for line in f:
		split_line=[]
		split_line=line.split(';')
		print(len(split_line))
		if len(split_line)==Register_Fields:
			#If the array has the exact fields elements to be processed into the query, cannot be less than the expected fields.
			SEngine=split_line[0]
			RDescription=split_line[1]
			RUrl=split_line[2]
			RDomain=split_line[3]
			RTerm=split_line[4]
			RTags=split_line[5]
			RLang=split_line[6]
			RIndexDate=split_line[7]
			RTorVer=split_line[8]
			DB_Driver=GraphDatabase.driver(DB_URI,auth=(DB_Username,DB_Password))
			c_query="MERGE (n:Searcher {name:'" + SEngine + "'}) ON CREATE SET n.created=timestamp()"
			session=DB_Driver.session()
			session.run(c_query)
			c_query="MERGE (n:SearchTerm {term:'" + RTerm + "'}) ON CREATE SET n.created=timestamp()"
			session.run(c_query)
			if len(RTags)>0:
				c_query="MERGE (n:TorNode:" + RTags.replace(u'\ufeff', '') + " {Domain:'" + RDomain + "', torVersion:'" + RTorVer + "'}) ON CREATE SET n.created=timestamp()"
			else:
				c_query="MERGE (n:TorNode {Domain:'" + RDomain + "', torVersion:'" + RTorVer + "'}) ON CREATE SET n.cretead=timestamp()"
			session.run(c_query)
			c_query="MERGE (n:Url {link:'" + RUrl.replace('\'','') + "', lang:'" + RLang + "'}) ON CREATE SET n.indexed=timestamp()"
			session.run(c_query)
			#Then create the relations between all nodes 
			c_query="MATCH (n:Searcher {name:'" + SEngine + "'}), (r:Url {link:'" + RUrl.replace('\'','') + "'}) MERGE (n) - [:Result {SearchedTerm:'" + RTerm + "'}] -> (r)"
			session.run(c_query)
			c_query="MATCH (n:TorNode {Domain:'" + RDomain + "'}), (r:Url {link:'" + RUrl.replace('\'','') + "'}) MERGE (n) - [:Host] -> (r)"
			session.run(c_query)
			c_query="MATCH (s:SearchTerm {term:'" + RTerm + "'}), (r:Url {link:'" + RUrl.replace('\'','') + "'}) MERGE (s) - [:Results] -> (r)"
			session.run(c_query)
			c_query="MATCH (r:Url {link:'" + RUrl.replace('\'','') + "'}) SET r.Description='" + RDescription.replace('\'','') + "'"
			
			session.run(c_query.replace('\\','')) 	
			DB_Driver.close()
	f.close()			
			
		


#Main Function
words_file = open(Words_File_Name,'r')
words=words_file.readlines()

for word in words:
	Cmd_Line=""
	Cmd_Line='onionsearch "' + word + '" --continuous_write True --fields engine name link domain --field_delimiter "' + ';' + '" --limit 100000'
	Cmd_Line=Cmd_Line.replace("\n","")
	os.system(Cmd_Line) 
words_file.close()
os.system('bash Normalize.sh')
Normalize_Whole_Results(Normalized_File_Name)
Insert_Into_Log4J("New_All_Sites_" + Date.strftime("%d%m%y") + ".csv")



hosts_file=open('all_hosts.csv','r')
hosts=hosts_file.readlines()
for host in hosts:
	DB_Driver=GraphDatabase.driver(DB_URI,auth=(DB_Username,DB_Password))
	c_query="CREATE (n:Node {name:'" + host + "'})"
	session=DB_Driver.session()
	session.run(c_query)
	DB_Driver.close()
hosts_file.close()
