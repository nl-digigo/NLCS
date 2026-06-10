#!/usr/bin/perl
# Genereer objecten-vergelijking 5.0 vs 5.2 voor EEN hoofdgroep.
#
# Gebruik:  perl code/genereer-vergelijking.pl BV
#
# - 5.2-bron : tabellen/publicatie/objectentabellen/objecten-concept-5.2-<CODE>.csv  (komma)
# - 5.0-bron : ~/Downloads/NLCS-OBJECTEN-<CODE>-5.0.csv                              (puntkomma, met BOM)
# - output   : ontwikkeling/heroverweging-5-2/<CODE>/objecten-vergelijking-<CODE>.html
#
# De 5.0-kolommen worden via %MAP hernoemd naar de 5.2-namen; alleen kolommen die
# (na mapping) in beide voorkomen worden vergeleken. Matching op id_nummer.
# Nieuwe rij = groen, gewijzigde cel = blauw (met "5.0: x / 5.2: y"),
# aparte tabel onderaan met verdwenen rijen.
#
# Uitzondering: in de kolom kind_van betekent "0" in 5.0 hetzelfde als leeg in 5.2
# (top-level object) -> dat telt NIET als wijziging.

use strict;
use warnings;
use Text::ParseWords;
binmode(STDOUT, ":encoding(UTF-8)");

my $CODE = shift @ARGV or die "Geef een hoofdgroep-code op, bv: perl code/genereer-vergelijking.pl BV\n";
my $OLDLAB = "5.0";

my $NEW = "tabellen/publicatie/objectentabellen/objecten-concept-5.2-$CODE.csv";
my $HOME = $ENV{HOME} // $ENV{USERPROFILE};
my $OLD = "$HOME/Downloads/NLCS-OBJECTEN-$CODE-5.0.csv";
my $OUTDIR = "ontwikkeling/heroverweging-5-2/$CODE";
my $OUT = "$OUTDIR/objecten-vergelijking-$CODE.html";
die "5.2-bestand niet gevonden: $NEW\n" unless -f $NEW;
die "5.0-bestand niet gevonden: $OLD\n" unless -f $OLD;
mkdir $OUTDIR unless -d $OUTDIR;

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

sub esc { my $s = shift; $s //= ""; $s =~ s/&/&amp;/g; $s =~ s/</&lt;/g; $s =~ s/>/&gt;/g; $s =~ s/"/&quot;/g; $s =~ s/'/&#x27;/g; return $s; }
sub cellv { my $s = shift; (defined $s && length $s) ? esc($s) : "<em>(leeg)</em>"; }
sub trim { my $s = shift; $s //= ""; $s =~ s/^\s+|\s+$//g; return $s; }
# kind_van: "0" in 5.0 == leeg in 5.2 (top-level object)
sub norm { my ($h, $v) = @_; $v = "" if $h eq "kind_van" && $v eq "0"; return $v; }

# Kolommen die nooit als "gewijzigd" gemarkeerd worden:
# id_nummer (de sleutel) en laagnaam (wordt genegeerd in de vergelijking).
my %SKIP = (id_nummer => 1, laagnaam => 1);

# --- 5.2 inlezen (komma; auto-detect puntkomma voor de zekerheid) ---
open(my $n, "<:encoding(UTF-8)", $NEW) or die $!;
my $hl = <$n>; $hl =~ s/^\x{FEFF}//; $hl =~ s/\r?\n$//;
my $sep = ($hl =~ /,/) ? "," : ";";
my @H = $sep eq "," ? parse_line(",", 0, $hl) : split(/;/, $hl, -1);
@H = map { trim($_) } @H;
my %HI; $HI{$H[$_]} = $_ for 0 .. $#H;
my @NR;
while (<$n>) { s/\r?\n$//; next unless length; push @NR, [ $sep eq "," ? parse_line(",", 0, $_) : split(/;/, $_, -1) ]; }
close $n;

# --- 5.0 inlezen (puntkomma + BOM), kolommen hernoemen via %MAP ---
open(my $o, "<:encoding(UTF-8)", $OLD) or die $!;
my $oh = <$o>; $oh =~ s/^\x{FEFF}//; $oh =~ s/\r?\n$//;
my @OH = map { $MAP{$_} // $_ } split(/;/, $oh, -1);
my %OI; for (0 .. $#OH) { $OI{$OH[$_]} = $_ unless exists $OI{$OH[$_]}; }
my @OR;
while (<$o>) { s/\r?\n$//; next unless length; push @OR, [ split(/;/, $_, -1) ]; }
close $o;

my %nset = map { $_ => 1 } @H;
my %common = map { $_ => 1 } grep { $nset{$_} } @OH;
my $oid = $OI{id_nummer};
my %L;
for my $r (@OR) { my $id = trim($r->[$oid]); $L{$id} = $r if length $id; }

@NR = sort { lc($a->[0] // "") cmp lc($b->[0] // "") } @NR;
my $nid = $HI{id_nummer};

my ($chg, $new, $rem) = (0, 0, 0);
my %matched;
my @out;
push @out, "<!DOCTYPE html>\n<html lang=\"nl\">\n<head>\n<meta charset=\"utf-8\">\n<title>Objecten vergelijking $OLDLAB vs 5.2 - $CODE</title>\n<style>\n" .
  "  body { font-family: Arial, sans-serif; margin: 20px; }\n  h1,h2 { color:#333; }\n" .
  "  .legend span { padding:4px 12px; margin-right:10px; border-radius:3px; font-size:14px; border:1px solid #bbb; }\n" .
  "  .changed { background-color:#cfe2ff; } .new-row { background-color:#d4edda; } .removed { background-color:#f8d7da; }\n" .
  "  .stats { margin:10px 0; font-size:14px; color:#555; }\n" .
  "  table { border-collapse:collapse; width:100%; font-size:12px; margin-bottom:30px; }\n" .
  "  th,td { border:1px solid #ccc; padding:5px 7px; text-align:left; vertical-align:top; }\n" .
  "  th { background:#f0f0f0; position:sticky; top:0; z-index:1; }\n  td.changed { white-space:nowrap; } .old { color:#666; }\n" .
  "  tr:hover td { background:#f5f5f5; } tr.new-row:hover td { background:#c3e6cb; }\n</style>\n</head>\n<body>\n" .
  "<h1>Objecten vergelijking $OLDLAB vs 5.2 - $CODE</h1>\n" .
  "<div class=\"legend\"><span class=\"new-row\">Nieuw in 5.2</span><span class=\"changed\">Gewijzigde cel ($OLDLAB &rarr; 5.2)</span><span class=\"removed\">Verdwenen in 5.2</span></div>\n<!--STATS-->\n";

push @out, "<table>\n<thead><tr>";
push @out, "<th>" . esc($_) . "</th>" for @H;
push @out, "</tr></thead>\n<tbody>\n";

for my $r (@NR) {
  my $id = trim($r->[$nid]);
  my $old = $L{$id};
  my $isnew = !defined $old;
  $matched{$id} = 1 unless $isnew;
  my @cells;
  for my $h (@H) {
    my $v = trim($r->[$HI{$h}]);
    if (!$isnew && $common{$h} && !$SKIP{$h}) {
      my $ov = trim($old->[$OI{$h}]);
      if (norm($h, $ov) ne norm($h, $v)) {
        $chg++;
        push @cells, "<td class=\"changed\" title=\"$OLDLAB: " . esc($ov) . "\"><span class=\"old\">$OLDLAB: " . cellv($ov) . "</span><br>5.2: " . cellv($v) . "</td>";
        next;
      }
    }
    push @cells, "<td>" . esc($v) . "</td>";
  }
  if ($isnew) { $new++; push @out, "<tr class=\"new-row\">" . join("", @cells) . "</tr>\n"; }
  else        {         push @out, "<tr>" . join("", @cells) . "</tr>\n"; }
}
push @out, "</tbody>\n</table>\n";

my @removed = grep { !$matched{ trim($_->[$oid]) } } @OR;
@removed = sort { lc($a->[$OI{omschrijving}] // "") cmp lc($b->[$OI{omschrijving}] // "") } @removed;
$rem = scalar @removed;
push @out, "<h2>Verdwenen in 5.2 ($rem)</h2>\n";
if ($rem) {
  push @out, "<table class=\"removed\">\n<thead><tr>";
  push @out, "<th>" . esc($_) . "</th>" for @OH;
  push @out, "</tr></thead>\n<tbody>\n";
  for my $r (@removed) {
    my @c = map { "<td>" . esc(trim($r->[$_])) . "</td>" } 0 .. $#OH;
    push @out, "<tr class=\"removed\">" . join("", @c) . "</tr>\n";
  }
  push @out, "</tbody>\n</table>\n";
} else {
  push @out, "<p>Geen.</p>\n";
}
push @out, "\n</body>\n</html>";

my $stats = "Gewijzigde cellen: $chg | Nieuwe rijen: $new | Verdwenen rijen: $rem";
my $full = join("", @out);
$full =~ s/<!--STATS-->/<div class="stats">$stats<\/div>/;
open(my $w, ">:encoding(UTF-8)", $OUT) or die $!;
print $w $full;
close $w;
print "WROTE $OUT\n$stats\n";
