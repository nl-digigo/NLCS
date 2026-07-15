#!/usr/bin/perl
# Vul de sobject-kolom van een objectentabel (5.2) aan voor onderliggende
# objecten waarvoor een symbool bestaat.
#
# Regel:
#   - Een objectrij krijgt een sobject-zoekfilter als:
#       * sobject leeg is, EN
#       * element == "G" (puur gebied), EN
#       * de zoekfilter "S<HG>-<subobject01>_<subobject02>..." overeenkomt met
#         een bestaand symbool (svg/dwg in de symbolenmap).
#   - Dan: sobject = die zoekfilter; element "G" -> "G/S"; laagnaam-suffix "-G" -> "-G/S".
#
# De zoekfilter wordt opgebouwd uit S<HG> + de subobjecten (NIET het object):
#   GESLOTENVERHARDING_ASFALT (sub01=ASFALT)            -> SVH-ASFALT
#   GESLOTENVERHARDING_ASFALT_FREESVAK (sub01,sub02)    -> SVH-ASFALT_FREESVAK
#
# Gebruik (dry-run):  perl vul_sobject.pl VH <symbolenmap>
#        (toepassen):  perl vul_sobject.pl VH <symbolenmap> --apply
#
use strict;
use warnings;
use Text::ParseWords;
binmode(STDOUT, ":encoding(UTF-8)");

my $HG     = shift @ARGV or die "Gebruik: perl $0 <HG> <symbolenmap> [--apply]\n";
my $SYMDIR = shift @ARGV or die "Gebruik: perl $0 <HG> <symbolenmap> [--apply]\n";
my $APPLY  = (grep { $_ eq "--apply" } @ARGV) ? 1 : 0;
my $SCODE  = "S$HG";

my $OBJ = "tabellen/publicatie/objectentabellen/objecten-concept-5.2-$HG.csv";
die "Objecttabel niet gevonden: $OBJ\n" unless -f $OBJ;
die "Symbolenmap niet gevonden: $SYMDIR\n" unless -d $SYMDIR;

sub trim { my $s = shift; $s //= ""; $s =~ s/^\s+|\s+$//g; return $s; }

# --- symbol-zoekfilters verzamelen (strip V-/B- en het element-suffix) ---
my %SYM;
opendir(my $dh, $SYMDIR) or die "$SYMDIR: $!";
for my $f (readdir $dh) {
  next unless $f =~ /\.(svg|dwg)$/i;
  (my $stem = $f) =~ s/\.(svg|dwg)$//i;
  $stem =~ s/^[BV]-//;              # variant-prefix weg
  $stem =~ s/-[A-Za-z0-9]+$//;      # element-suffix (-SO, -D, ...) weg
  $SYM{$stem} = 1 if length $stem;
}
closedir $dh;

# --- objecttabel inlezen (komma; kolommen 1..27 zijn veilig, geen ingebedde komma's) ---
open(my $in, "<:encoding(UTF-8)", $OBJ) or die "$OBJ: $!";
my @lines = <$in>;
close $in;
chomp @lines;
my $hl = $lines[0]; $hl =~ s/^\x{FEFF}//;
my @H = split /,/, $hl, -1;
my %HI; for (0 .. $#H) { $HI{$H[$_]} = $_ unless exists $HI{$H[$_]}; }
my @SUBI = map { $HI{"subobject0$_"} } (1..5);
my ($EI, $SOI, $LI) = @HI{qw(element sobject laagnaam)};
die "Vereiste kolommen ontbreken\n" unless defined $EI && defined $SOI && defined $LI;

# laagnaam -> objectpad (tussen '*-**-<HG>-' en het element-suffix)
sub pathof {
  my ($laag, $el) = @_;
  $laag = trim($laag); $el = trim($el);
  $laag =~ s/^\*-\*\*-\Q$HG\E-//;
  $laag =~ s/-\Q$el\E$// if length $el;
  return $laag;
}

# --- huidige sobject per objectpad (ouder-lookup) ---
my %soByPath;
for my $i (1 .. $#lines) {
  next unless length $lines[$i] && $lines[$i] =~ /\S/;
  my @f = split /,/, $lines[$i], -1;
  my $so = trim($f[$SOI] // "");
  next unless length $so;
  $soByPath{ pathof($f[$LI], $f[$EI]) } = $so;
}

# --- aanvullen: ouder-sobject + laatste laagnaam-segment; herhaald tot niets meer verandert ---
my @fill;
my %done;
my $round = 1;
while (1) {
  my $changed = 0;
  for my $i (1 .. $#lines) {
    next if $done{$i};
    next unless length $lines[$i] && $lines[$i] =~ /\S/;
    my @f = split /,/, $lines[$i], -1;
    next if length trim($f[$SOI] // "");   # al gevuld
    next unless trim($f[$EI] // "") eq "G"; # alleen puur gebied
    my $path = pathof($f[$LI], "G");
    next unless $path =~ /_/;                # geen ouder mogelijk
    (my $parent = $path) =~ s/_([^_]+)$//;
    my $lastseg = $1;
    my $pso = $soByPath{$parent};
    next unless defined $pso && length $pso; # ouder heeft geen zoekfilter
    my $cand = "${pso}_${lastseg}";
    next unless $SYM{$cand};                 # alleen als het symbool echt bestaat
    push @fill, { idx => $i, cand => $cand, path => $path, oms => trim($f[0] // "") };
    $soByPath{$path} = $cand;                # zodat diepere kinderen kunnen aanhaken
    $done{$i} = 1;
    $changed = 1;
  }
  last unless $changed;
  $round++;
}

print "== AAN TE VULLEN: ", scalar(@fill), " rijen (element G -> G/S, sobject ingevuld) ==\n";
for my $r (@fill) {
  printf "  %-45s -> sobject=%s\n", $r->{oms}, $r->{cand};
}
print "\n";

if (!$APPLY) { print "(dry-run; voeg --apply toe om te schrijven)\n"; exit 0; }

# --- toepassen ---
my %fillset = map { $_->{idx} => $_->{cand} } @fill;
for my $i (keys %fillset) {
  my @f = split /,/, $lines[$i], -1;
  $f[$SOI] = $fillset{$i};
  # element G -> G/S
  $f[$EI] = "G/S" if trim($f[$EI]) eq "G";
  # laagnaam: laatste '-G' -> '-G/S'
  $f[$LI] =~ s/-G$/-G\/S/;
  $lines[$i] = join(",", @f);
}
open(my $out, ">:encoding(UTF-8)", $OBJ) or die "$OBJ: $!";
print $out join("\n", @lines), "\n";
close $out;
print "TOEGEPAST: ", scalar(@fill), " rijen bijgewerkt in $OBJ\n";
