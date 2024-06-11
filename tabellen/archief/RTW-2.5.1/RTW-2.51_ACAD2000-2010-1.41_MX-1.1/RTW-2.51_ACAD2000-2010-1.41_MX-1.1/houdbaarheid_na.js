// file and path  : houdbaarheid_na.js
// version        : 2.1
// version release: 09-10-2001
// version release: 21-05-2001
// designer       : C.J.F. Rothfusz
// company        : Tree C Technology B.V.

//Geldigheidstermijn kan hier voor alle richtlijnen worden ingesteld.
//Verander na 31-12-1999 de 19 in de laatste regel in 20.
function makeArray() {
  for (i = 0; i<makeArray.arguments.length; i++)
  this[i + 1] = makeArray.arguments[i];
}
var months = new makeArray('Januari','Februari','Maart','April','Mei','Juni','Juli','Augustus','September','Oktober','November','December');
function y2k(number) { return (number < 1000) ? number + 1900 : number; }
function optel(number) { return (number < 100) ? number + 1900 : number; }
function monthsahead(noofmonths) {
  var today = new Date();
  var date = new Date(today.getYear(),today.getMonth() + noofmonths,today.getDate(),today.getHours(),today.getMinutes(),today.getSeconds());
  var Datum = date.getDate() + '-' + months[date.getMonth() + 1] + '-' + y2k(optel(date.getYear()));
  return Datum;
}
document.write('<br>Deze richtlijn is na afdrukken geldig tot 6 maanden na ')
document.write(monthsahead(0));
document.write('<br>Voor deze richtlijn gelden bepalingen ten aanzien van wijzigen en verspreiden.<br> Zie de <b>gebruiksbepalingen.</b><br>Copyright©: Rijkswaterstaat')
document.write('</font>')
