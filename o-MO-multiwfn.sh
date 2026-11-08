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
 
  iif=${ii::-1}
  echo -e "5 \n4 \nh \n3 \n2 \n0 \nq" | Multiwfn ${ii}dft.gbw > log
  mv MOvalue.cub homo-${iif}.cub
  echo -e "5 \n4 \nl \n3 \n2 \n0 \nq" | Multiwfn ${ii}dft.gbw > log
  mv MOvalue.cub lumo-${iif}.cub 

  fi 
  done
  echo done!!!
 fi
else
 #multiwfn orders: 5,4,MO,3 high-grid, 2 export
  echo -e "5 \n4 \nh \n3 \n2 \n0 \nq" | Multiwfn $1 > log
  mv MOvalue.cub homo.cube
  echo -e "5 \n4 \nl \n3 \n2 \n0 \nq" | Multiwfn $1 > log
  mv MOvalue.cub lumo.cube

fi
