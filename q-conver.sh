#!/bin/bash
if [ $# -lt 1 ]
then
   echo usage: $0 filename.out
else
   grep -B4 'number of scf cycles' $1
   echo "=================================="
   nstep=$(grep 'number of scf cycles' $1 | tail -1 | awk '{print $6}')
   NE=$(grep 'number of electrons' $1 | awk '{print $5}')
   NB=$(grep 'number of Kohn-Sham states' $1 | awk '{print $5}')
   echo "nelectrons= "$NE, "nbands= "$NB
   echo "=================================="
   grep 'converged in' $1

  if [[ ! $nstep =~ ^[0-9]+$ ]] ; then
   echo "==> elec step convergence: "
   grep 'iteration' $1 | tail -7
  fi

  NATOM=$(grep 'number of atoms/cell' $1 | tail -1 | awk '{print $5}')
  if [ $nstep -gt 0 ] 2>/dev/null
  then
   grep 'ATOMIC_POSITIONS' $1 -A $NATOM --no-group-separator | awk -v nat="$NATOM" '/ATOMIC_POSITIONS/{print nat; print "Frame " ++i; next} {print}' > opt.xyz
   echo "==>  OPT traj is stored in opt.xyz !"
  fi

  if grep 'Begin final coordinates' $1 > /dev/null; then
   sed -n '/Begin final coordinates/,/End final coordinates/{ /End/d; p}' $1 > tmp2
   if grep -A 3 'CELL_PARAMETERS' tmp2 > tmp1; then
    echo 'vc-relax case'
    cat tmp2 > xyz.tmp
   else
    grep -A 3 'CELL_PARAMETERS' *.in > tmp1
   fi
    echo 'CRYSTAL' > out.xsf
    echo 'PRIMVEC' >> out.xsf
    tail -3 tmp1 >> out.xsf
    echo 'PRIMCOORD' >> out.xsf
    echo $NATOM >> out.xsf
    tail -$NATOM tmp2 >> out.xsf
   rm tmp1 tmp2
   echo "==>  Final coordinates stored in out.xsf !"
   unix2dos out.xsf
  fi

fi
