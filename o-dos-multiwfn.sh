#!/bin/bash
if [ $# -lt 1 ]
then
 echo usage: $0 + orca.gbw.file
 echo or $0 search all dir
 echo -------processing--------
 list=`ls -F | grep "/"`
 if [ -z "$list" ]
 then
  echo no dir!!!
 else
  for ii in $list
  do

  if [ ! -f "${ii}dft.gbw" ]
  then
   echo extra file dir!!! no ${ii}dft.gbw
  else
 
  echo -e "\r \n 10\n 8\n-3\n 2\n-25,10,2\n 3\n0.1\n 0\n3\n0\n-10\nq" \
  | Multiwfn ${ii}dft.gbw > log
  iif=${ii::-1}
  mv DOS_curve.txt dos-${iif}.dat
  mv DOS_line.txt dosline-${iif}.dat 

  mv orginfo.txt orb-${iif}.txt

  fi 
  done
  echo done!!!
 fi
else
 #multiwfn orders: 10 dos, 8 unit, 2 set_xrange-[-25:10], 3 FWHM-0.05, 0 plot, 3 export
 echo -e "\r \n 10\n 8\n-3\n 2\n-25,10,2\n 3\n0.1\n 0\n3\n0\n-10\nq" | Multiwfn $1 > log
fi
