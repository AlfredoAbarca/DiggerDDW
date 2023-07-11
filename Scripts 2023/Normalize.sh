#!/bin/bash

out_fileName="All_Sites_"
date=`date +%d%m%y`
out_fileName="$out_fileName$date.csv"
old_fileName="Old_$out_fileName"
rm $out_fileName
rm $old_fileName
for file in `ls -tr *.txt`; do cat $file >> $out_fileName;done
cat $out_fileName | awk -F';' '{print $4}' | uniq > all_hosts.csv
sed -r '/^\s*$/d' all_hosts.csv > all_hosts2.csv
sed -r '/^.{,60}$/d' all_hosts2.csv > all_hosts3.csv
sed -r '/http:/d' all_hosts3.csv > all_hosts4.csv
sed -r '/https:/d' all_hosts4.csv > all_hosts5.csv
sed -r '/.onion/!d' all_hosts5.csv > all_hosts6.csv
cat all_hosts6.csv | sort | uniq > all_hosts.csv 
mv $out_fileName $old_fileName
cat $old_fileName | sort | uniq > $out_fileName
rm $old_fileName
