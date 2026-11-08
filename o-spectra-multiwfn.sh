#!/bin/bash
if [ $# -lt 1 ]
then
 echo usage: $0 + orca.out.file
 echo or $0 search all dir
 echo -------processing--------
 list=`ls -F | grep "/"`
 if [ -z "$list" ]
 then
  echo no dir!!!
 else
  for ii in $list
  do

  if [ ! -f "${ii}dft.out" ]
  then
   echo extra file dir!!! no ${ii}dft.out
  else
 
  echo -e "11\n 3\n 10\n -1\n 3\n 0,10,20\n 8\n 0.2\n 2\n -3\nq" \
  | Multiwfn ${ii}dft.out > log
  iif=${ii::-1}
  mv spectrum_curve.txt curve-${iif}.dat
  mv spectrum_line.txt line-${iif}.dat

  fi 
  done
  echo done!!!
 fi
else
 #multiwfn orders: 11 spcetra, 3 uv-vis, 10 unit, 3 set_xrange-[0:10], 8 FWHM-0.2, 2 export
 echo -e "11\n 3\n 10\n-1\n 3\n0,10,20\n 8\n0.25\n 2\n -3\nq" | Multiwfn $1 > log
fi
