#!/usr/bin/perl
# Genereer de docs/changelog symbolen-changelog voor EEN sbibliotheek in het
# "published" docs-format (docs/changelog/<HG>/NLCS_Query_Symbolen-concept-5.2-<SCODE>.html).
#
# Gebruik:  perl beheer/releasenotesmaken/genereer_changelog_symbolen.pl SVH
#
# Bronnen
# -------
# - 5.2   : tabellen/publicatie/NLCS_Query_Symbolen-concept-5.2.csv
#           (komma-gescheiden; kolommen: symboolURI,searchterm,sbibliotheek,fase,id,symbool,finalCleanName,optie)
# - 5.0.2 : <NLCSmain>/tabellen/publicatie/5.02-symbolen.csv
#           (elke regel is één dubbel-gequote veld met verdubbelde quotes;
#            kolommen: symboolURI,id,sbibliotheek,sbibliotheekURI,fase,symbool,optie,fileURL)
#
# Vergelijking UITSLUITEND op de symboolnaam (symbool); id wordt genegeerd.
#   - naam in 5.2 maar niet in 5.0.2   -> <tr class="new-row">  (groen)
#   - naam in 5.0.2 maar niet in 5.2   -> onder grijze section-header: <tr class="deleted">
#   - naam in beide                    -> gewone rij
# Een hernoemd symbool verschijnt dus als een verwijderde + een nieuwe regel.
# Rijvolgorde: alfabetisch op de symboolnaam.
#
# Output: docs/changelog/<HG>/NLCS_Query_Symbolen-concept-5.2-<SCODE>.html

use strict;
use warnings;
use Text::ParseWords;
binmode(STDOUT, ":encoding(UTF-8)");

my $SCODE  = shift @ARGV // "SVH";           # sbibliotheek, bv. SVH
my $HG     = ($SCODE =~ /^S(.+)$/) ? $1 : $SCODE;  # hoofdgroep-map, bv. VH
my $OLDLAB = "5.0.2";

my $NEW = "tabellen/publicatie/NLCS_Query_Symbolen-concept-5.2.csv";
my $NLCSMAIN = "C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCSmain/NLCS";
my $OLD = "$NLCSMAIN/tabellen/publicatie/5.02-symbolen.csv";
my $OUTDIR = "docs/changelog/$HG";
my $OUT = "$OUTDIR/NLCS_Query_Symbolen-concept-5.2-$SCODE.html";

die "5.2-bestand niet gevonden: $NEW\n" unless -f $NEW;
die "5.0.2-referentie niet gevonden: $OLD\n" unless -f $OLD;

sub esc { my $s = shift; $s //= ""; $s =~ s/&/&amp;/g; $s =~ s/</&lt;/g; $s =~ s/>/&gt;/g; return $s; }
sub trim { my $s = shift; $s //= ""; $s =~ s/^\s+|\s+$//g; return $s; }

# --- 5.2 inlezen (komma) ---
open(my $n, "<:encoding(UTF-8)", $NEW) or die "$NEW: $!";
my $hl = <$n>; $hl =~ s/^\x{FEFF}//; $hl =~ s/\r?\n$//;
my @H = map { trim($_) } parse_line(",", 0, $hl);
my %HI; for (0 .. $#H) { $HI{$H[$_]} = $_ unless exists $HI{$H[$_]}; }
for my $need (qw(sbibliotheek id symbool searchterm)) {
  die "Kolom '$need' ontbreekt in $NEW\n" unless exists $HI{$need};
}
my ($NSB, $NID, $NSYM, $NST) = @HI{qw(sbibliotheek id symbool searchterm)};
my @NR;
while (<$n>) {
  s/\r?\n$//; next unless length && /\S/;
  my @f = parse_line(",", 0, $_);
  next unless defined $f[$NSB] && trim($f[$NSB]) eq $SCODE;
  push @NR, [ @f ];
}
close $n;

# Sorteren uitsluitend op de symboolnaam (niet op id).
@NR = sort { lc(trim($a->[$NSYM] // "")) cmp lc(trim($b->[$NSYM] // "")) } @NR;

# --- 5.0.2 inlezen (dubbel-gequote regels) ---
open(my $o, "<:encoding(UTF-8)", $OLD) or die "$OLD: $!";
my @raw;
while (my $line = <$o>) { $line =~ s/^\x{FEFF}//; $line =~ s/\r?\n$//; push @raw, $line if length $line && $line =~ /\S/; }
close $o;

sub split_50 {
  my $line = shift;
  $line =~ s/^"//; $line =~ s/"$//;
  $line =~ s/""/"/g;
  return parse_line(",", 0, $line);
}
my @OH = map { trim($_) } split_50($raw[0]);
my %OI; for (0 .. $#OH) { $OI{$OH[$_]} = $_ unless exists $OI{$OH[$_]}; }
for my $need (qw(sbibliotheek id symbool)) {
  die "Kolom '$need' ontbreekt in referentie $OLD\n" unless exists $OI{$need};
}
my ($OSB, $OID, $OSYM) = @OI{qw(sbibliotheek id symbool)};
my (%OLDNAME, @OROWS);
for my $i (1 .. $#raw) {
  my @f = map { trim($_) } split_50($raw[$i]);
  next unless defined $f[$OSB] && $f[$OSB] eq $SCODE;
  push @OROWS, [ @f ];
  my $nm = trim($f[$OSYM]);
  $OLDNAME{$nm} = 1 if length $nm;
}

# --- HTML opbouwen ---
my $new = 0;
my @out;

my $head = <<"HEAD";
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NLCS_Query_Symbolen-concept-5.2-$SCODE</title>
  <style>
    body { font-family: Arial, sans-serif; font-size: 13px; margin: 20px; }
    h1 { font-size: 1.2em; margin-bottom: 10px; }
    table { border-collapse: collapse; width: 100%; }
    th { background-color: #003865; color: white; text-align: left;
          padding: 6px 8px; white-space: nowrap; }
    td { border: 1px solid #ccc; padding: 4px 8px; vertical-align: top; }
    tr:nth-child(even) td { background-color: #f2f2f2; }
    tr:hover td { background-color: #dde8f0; }
    .new-row td    { background-color: #d4edda !important; }
    .new-row:hover td { background-color: #b8dfc4 !important; }
    .changed       { background-color: #cce5ff !important; }
    .old-val { color: #555; font-size: 0.85em; }
    .new-val { font-weight: normal; }
    .section-header td { background-color: #a0a0a0 !important;
                          color: white; font-weight: bold; padding: 4px 8px; }
    .deleted td    { background-color: #d0d0d0 !important; }
    .deleted:hover td { background-color: #b8b8b8 !important; }
  </style>
</head>
<body>
  <h1>NLCS_Query_Symbolen-concept-5.2-$SCODE</h1>
  <!-- legenda -->
  <div style="margin-bottom:12px;font-size:12px;display:flex;gap:16px;flex-wrap:wrap;">
    <span style="background:#d4edda;border:1px solid #b8dfc4;padding:2px 8px;border-radius:3px;">Nieuw in versie 5.2</span>
    <span style="background:#d0d0d0;border:1px solid #aaa;padding:2px 8px;border-radius:3px;">Aanwezig in 5.0.2, verwijderd in 5.2</span>
  </div>
  <table>
HEAD
push @out, $head;
push @out, "    <thead><tr>" . join("", map { "<th>" . esc($_) . "</th>" } @H) . "</tr></thead>\n";
push @out, "    <tbody>\n";

for my $r (@NR) {
  my $nm = trim($r->[$NSYM]);
  my $isnew = !(length $nm && $OLDNAME{$nm});
  my @cells = map { "<td>" . esc(trim($r->[$HI{$_}])) . "</td>" } @H;
  if ($isnew) { $new++; push @out, "      <tr class=\"new-row\">" . join("", @cells) . "</tr>\n"; }
  else        {         push @out, "      <tr>" . join("", @cells) . "</tr>\n"; }
}

# Verdwenen rijen (naam in 5.0.2, niet in 5.2), alfabetisch op naam, in de 5.2-kolomindeling.
my %NEWNAME = map { trim($_->[$NSYM]) => 1 } @NR;
my @removed = grep { my $nm = trim($_->[$OSYM]); length $nm && !$NEWNAME{$nm} } @OROWS;
@removed = sort { lc($a->[$OSYM] // "") cmp lc($b->[$OSYM] // "") } @removed;
if (@removed) {
  my $cols = scalar @H;
  push @out, "      <tr class=\"section-header\"><td colspan=\"$cols\">Aanwezig in versie 5.0.2 &ndash; verwijderd in versie 5.2</td></tr>\n";
  for my $r (@removed) {
    my @cells;
    for my $h (@H) {
      # map 5.0.2-kolom naar 5.2-kolom als die bestaat; anders leeg (searchterm/finalCleanName)
      my $v = exists $OI{$h} ? trim($r->[$OI{$h}]) : "";
      push @cells, "<td>" . esc($v) . "</td>";
    }
    push @out, "      <tr class=\"deleted\">" . join("", @cells) . "</tr>\n";
  }
}

push @out, "    </tbody>\n  </table>\n</body>\n</html>\n";

mkdir $OUTDIR unless -d $OUTDIR;
open(my $w, ">:encoding(UTF-8)", $OUT) or die "$OUT: $!";
print $w join("", @out);
close $w;

print "5.2-bron    : $NEW\n";
print "5.0.2-bron  : $OLD\n";
print "WROTE $OUT\n";
print "  sbibliotheek $SCODE | 5.2-rijen: ", scalar(@NR), " | 5.0.2-rijen: ", scalar(@OROWS), "\n";
print "  nieuwe namen: $new | verdwenen namen: ", scalar(@removed), " (vergelijking uitsluitend op naam)\n";
