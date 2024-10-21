VE=new Array
VE[1]="RTW-2.51_ACAD-2000(i)/2010-1.41_MX-1.1"	
VE[2]="RTW-2.51_ACAD-2000(i)/2010-1.41_MX-1.1"
VE[3]="RTW-2.51_ACAD-2000(i)/2010-1.41_MX-1.1"
VE[4]="TB 1.51"
DIS=new Array
DIS[1]="wegen"
DIS[2]="kunstwerken"
DIS[3]="waterbouw"
DIS[4]="beton"
DIS[5]="staal"
DIS[6]="water"
DIS[7]="werkt"
DIS[8]="geen"

function GeefVersie(i) {
  return VE[i]
}

function leeg(x) {
  for (k=0;k<x;k++) document.write('&nbsp;');
}

function GeefDiscipline(i) {
  return DIS[i]
}

var disc = parent.database.disc
var vers = parent.database.vers
var subdisc = parent.database.subdisc
