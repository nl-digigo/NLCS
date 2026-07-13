#!/usr/bin/perl
# Genereer de docs/changelog objecten-changelog voor EEN hoofdgroep in het
# "published" docs-format (zoals docs/changelog/<CODE>/objecten-concept-5.2-<CODE>.html).
#
# Gebruik:  perl beheer/releasenotesmaken/genereer_changelog_objecten.pl KL
#
# Bronnen
# -------
# - 5.2 : tabellen/publicatie/objectentabellen/objecten-concept-5.2-<CODE>.csv
#         Scheidingsteken wordt automatisch gedetecteerd (komma of puntkomma).
#         LET OP: sommige hoofdgroepen (o.a. KL) zijn nog puntkomma-gescheiden.
# - 5.0.2 referentie (in deze voorkeursvolgorde):
#     1. ~/Downloads/NLCS-OBJECTEN-<CODE>-5.0.csv     (volledige export, puntkomma, BOM)
#     2. <NLCSmain>/tabellen/publicatie/objectentabellen-verkort/
#        5.02-Objectentabel-<CODE>-*.csv              (verkorte tabel, dubbel-gequote komma)
#
# Output
# ------
# docs/changelog/<CODE>/objecten-concept-5.2-<CODE>.html
#
# Opmaak (identiek aan de bestaande docs-changelogs)
# --------------------------------------------------
# - Volledige 5.2-tabel, alfabetisch gesorteerd op de eerste kolom (omschrijving).
# - Nieuwe rij (id_nummer niet in 5.0.2)     -> <tr class="new-row"> (groen)
# - Gewijzigde cel (zelfde id, andere waarde) -> <td class="changed"> met
#       <div class="old-val">5.0.2: x</div><div class="new-val">5.2&#58; y</div>
# - Onderaan, in dezelfde tabel, onder een grijze <tr class="section-header">:
#   de verdwenen rijen (id wel in 5.0.2, niet in 5.2) als <tr class="deleted">.
#
# Matching op id_nummer. Vergeleken worden alleen kolommen die (na hernoemen van
# de 5.0-koppen via %MAP) in BEIDE bestanden voorkomen. Uitzonderingen die NIET
# als wijziging tellen: id_nummer en laagnaam (%SKIP); kind_van "0"==leeg;
# leidend "LETTERS:" prefix in aobject/sobject.

use strict;
use warnings;
use Text::ParseWords;
binmode(STDOUT, ":encoding(UTF-8)");

my $CODE   = shift @ARGV // "KL";
my $OLDLAB = "5.0.2";

my $NEW = "tabellen/publicatie/objectentabellen/objecten-concept-5.2-$CODE.csv";
my $HOME = $ENV{HOME} // $ENV{USERPROFILE};
my $OLD_EXPORT = "$HOME/Downloads/NLCS-OBJECTEN-$CODE-5.0.csv";
my $NLCSMAIN = "../../NLCSmain/NLCS";
my $VERKORT_DIR = "$NLCSMAIN/tabellen/publicatie/objectentabellen-verkort";
my $OUTDIR = "docs/changelog/$CODE";
my $OUT = "$OUTDIR/objecten-concept-5.2-$CODE.html";

die "5.2-bestand niet gevonden: $NEW\n" unless -f $NEW;

# 5.0.2-referentie kiezen.
my $OLD;
if (-f $OLD_EXPORT) {
  $OLD = $OLD_EXPORT;
} else {
  my @m = sort glob("$VERKORT_DIR/5.02-Objectentabel-$CODE-*.csv");
  die "Geen 5.0.2-referentie gevonden: noch $OLD_EXPORT, noch 5.02-Objectentabel-$CODE-*.csv in $VERKORT_DIR\n"
    unless @m;
  $OLD = $m[0];
}

my %MAP = (
  OMSCHRIJVING=>"omschrijving", STATUS=>"status", DISCIPLINE=>"discipline", HOOFDGROEP=>"hoofdgroep",
  OBJECT=>"object", SUBOBJECT01=>"subobject01", SUBOBJECT02=>"subobject02", SUBOBJECT03=>"subobject03",
  SUBOBJECT04=>"subobject04", SUBOBJECT05=>"subobject05", BEWERKING=>"bewerking", ELEMENT=>"element",
  SCHAAL=>"schaal", ARCERING=>"aobject", SYMBOOL=>"sobject", LAAGNAAM=>"laagnaam",
  "B lineweight"=>"lw_b","B color"=>"kl_b","B color A"=>"kl_b_a","B color GD"=>"kl_b_gd","B color GN"=>"kl_b_gn","B color V"=>"kl_b_v","B linetype"=>"lt_b",
  "N lineweight"=>"lw_n","N color"=>"kl_n","N color A"=>"kl_n_a","N color GD"=>"kl_n_gd","N color GN"=>"kl_n_gn","N color V"=>"kl_n_v","N linetype"=>"lt_n",
  "V lineweight"=>"lw_v","V color"=>"kl_v","V color A"=>"kl_v_a","V color GD"=>"kl_v_gd","V color GN"=>"kl_v_gn","V color V"=>"kl_v_v","V linetype"=>"lt_v",
  "T lineweight"=>"lw_t","T color"=>"kl_t","T color A"=>"kl_t_a","T color GD"=>"kl_t_gd","T color GN"=>"kl_t_gn","T color V"=>"kl_t_v","T linetype"=>"lt_t",
  VRKL_kort=>"vrkl_kort", VRKL_lang=>"vrkl_lang", ID=>"id_nummer", KIND_VAN=>"kind_van",
);

my %SKIP = (id_nummer => 1, laagnaam => 1);

sub esc { my $s = shift; $s //= ""; $s =~ s/&/&amp;/g; $s =~ s/</&lt;/g; $s =~ s/>/&gt;/g; return $s; }
sub trim { my $s = shift; $s //= ""; $s =~ s/^\s+|\s+$//g; return $s; }

# Normalisatie vóór vergelijken (telt niet als wijziging).
sub norm {
  my ($h, $v) = @_;
  $v = "" if $h eq "kind_van" && $v eq "0";
  $v =~ s/^[A-Za-z]+:// if $h eq "aobject" || $h eq "sobject";
  return $v;
}

# --- 5.2 inlezen (komma of puntkomma; autodetect) ---
open(my $n, "<:encoding(UTF-8)", $NEW) or die "$NEW: $!";
my $hl = <$n>; $hl =~ s/^\x{FEFF}//; $hl =~ s/\r?\n$//;
my $sep = ($hl =~ /,/) ? "," : ";";
my @H = $sep eq "," ? parse_line(",", 0, $hl) : split(/;/, $hl, -1);
@H = map { trim($_) } @H;
my %HI; for (0 .. $#H) { $HI{$H[$_]} = $_ unless exists $HI{$H[$_]}; }
die "Kolom id_nummer ontbreekt in $NEW\n" unless exists $HI{id_nummer};
my @NR;
while (<$n>) {
  s/\r?\n$//; next unless length && /\S/;
  push @NR, [ $sep eq "," ? parse_line(",", 0, $_) : split(/;/, $_, -1) ];
}
close $n;

# --- 5.0.2 inlezen: verkorte dubbel-gequote tabel OF puntkomma-export ---
open(my $o, "<:encoding(UTF-8)", $OLD) or die "$OLD: $!";
my @raw;
while (my $line = <$o>) { $line =~ s/^\x{FEFF}//; $line =~ s/\r?\n$//; push @raw, $line if length $line && $line =~ /\S/; }
close $o;

# Echte kop = eerste regel met 'omschrijving' (ongeacht case). Regels ervoor
# (bv. een titelregel "KL-kabelsenleidingen") worden overgeslagen.
my $hidx = 0;
for my $i (0 .. $#raw) { if ($raw[$i] =~ /omschrijving/i) { $hidx = $i; last; } }
my $sample = $raw[$hidx];
my $double_quoted = ($sample =~ /^"/ && $sample =~ /""/);

sub split_50 {
  my $line = shift;
  if ($double_quoted) {
    $line =~ s/^"//; $line =~ s/"$//;
    $line =~ s/""/"/g;
    return parse_line(",", 0, $line);
  } elsif ($line =~ /;/) {
    return split(/;/, $line, -1);
  } else {
    return parse_line(",", 0, $line);
  }
}

my @OH = map { my $h = trim($_); $MAP{$h} // $h } split_50($raw[$hidx]);
my %OI; for (0 .. $#OH) { $OI{$OH[$_]} = $_ unless exists $OI{$OH[$_]}; }
die "Kolom id_nummer ontbreekt in referentie $OLD\n" unless exists $OI{id_nummer};
my @OR;
for my $i ($hidx+1 .. $#raw) { push @OR, [ map { trim($_) } split_50($raw[$i]) ]; }

# Gemeenschappelijke kolommen (na mapping), minus SKIP.
my %nset = map { $_ => 1 } @H;
my %common = map { $_ => 1 } grep { $nset{$_} && !$SKIP{$_} } @OH;

my $oid = $OI{id_nummer};
my %L;
for my $r (@OR) { my $id = trim($r->[$oid]); $L{$id} = $r if length $id; }

# 5.2-rijen alfabetisch op eerste kolom (omschrijving).
@NR = sort { lc($a->[0] // "") cmp lc($b->[0] // "") } @NR;
my $nid = $HI{id_nummer};

my ($chg, $new) = (0, 0);
my %matched;
my @out;

my $head = <<"HEAD";
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>objecten-concept-5.2-$CODE</title>
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
  <h1>objecten-concept-5.2-$CODE</h1>
  <!-- legenda -->
  <div style="margin-bottom:12px;font-size:12px;display:flex;gap:16px;flex-wrap:wrap;">
    <span style="background:#d4edda;border:1px solid #b8dfc4;padding:2px 8px;border-radius:3px;">Nieuw in versie 5.2</span>
    <span style="background:#cce5ff;border:1px solid #99caff;padding:2px 8px;border-radius:3px;">Gewijzigd ten opzichte van 5.0.2</span>
    <span style="background:#d0d0d0;border:1px solid #aaa;padding:2px 8px;border-radius:3px;">Aanwezig in 5.0.2, verwijderd in 5.2</span>
  </div>
  <table>
HEAD
push @out, $head;

push @out, "    <thead><tr>" . join("", map { "<th>" . esc($_) . "</th>" } @H) . "</tr></thead>\n";
push @out, "    <tbody>\n";

for my $r (@NR) {
  my $id = trim($r->[$nid]);
  my $old = $L{$id};
  my $isnew = !defined $old;
  $matched{$id} = 1 unless $isnew;
  my @cells;
  for my $h (@H) {
    my $ci = $HI{$h};
    my $v = trim($r->[$ci]);
    if (!$isnew && $common{$h}) {
      my $ov = trim($old->[$OI{$h}]);
      if (norm($h, $ov) ne norm($h, $v)) {
        $chg++;
        push @cells, "<td class=\"changed\"><div class=\"old-val\">$OLDLAB: " . esc($ov)
                   . "</div><div class=\"new-val\">5.2&#58; " . esc($v) . "</div></td>";
        next;
      }
    }
    push @cells, "<td>" . esc($v) . "</td>";
  }
  if ($isnew) { $new++; push @out, "      <tr class=\"new-row\">" . join("", @cells) . "</tr>\n"; }
  else        {         push @out, "      <tr>" . join("", @cells) . "</tr>\n"; }
}

# Verdwenen rijen (in 5.0.2, niet in 5.2), in de 5.2-kolomindeling.
my @removed = grep { my $id = trim($_->[$oid]); length $id && !$matched{$id} } @OR;
my $omi = $OI{omschrijving};
@removed = sort { lc(defined $omi ? ($a->[$omi] // "") : "") cmp lc(defined $omi ? ($b->[$omi] // "") : "") } @removed;

if (@removed) {
  my $cols = scalar @H;
  push @out, "      <tr class=\"section-header\"><td colspan=\"$cols\">Aanwezig in versie 5.0.2 &ndash; verwijderd in versie 5.2</td></tr>\n";
  for my $r (@removed) {
    my @cells;
    for my $h (@H) {
      my $oi = $OI{$h};
      my $v = defined $oi ? trim($r->[$oi]) : "";
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

print "5.2-bron    : $NEW  (scheiding: '$sep')\n";
print "5.0.2-bron  : $OLD  (", ($double_quoted ? "dubbel-gequote" : "plat"), ")\n";
print "WROTE $OUT\n";
print "  nieuwe rijen: $new | gewijzigde cellen: $chg | verdwenen rijen: ", scalar(@removed),
      " | totaal 5.2-rijen: ", scalar(@NR), "\n";
