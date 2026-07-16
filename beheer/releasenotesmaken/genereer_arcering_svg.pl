#!/usr/bin/perl
# Rendert NLCS-arceringen (AutoCAD hatch-patronen) naar SVG-swatches.
#
# Bron : tabellen/publicatie/NLCS_Query_Arceringen-concept-5.2.csv
#        kolommen o.a.: abibliotheek, fase, arcering, schaal, vrkl_lang
# vrkl_lang = een of meer lijnfamilies, gescheiden door spaties; elke familie:
#        hoek, x-origin, y-origin, delta-x, delta-y [, dash1, dash2, ...]
#        (positief = streep, negatief = gat, geen dashes = doorgetrokken)
#
# Gebruik:  perl genereer_arcering_svg.pl <ABIB> <doelmap>
#   bv.     perl genereer_arcering_svg.pl AVH docs/changelog/VH/AVH
#
# Filtert op abibliotheek == <ABIB>, laat vervallen (fase V of V-prefix) weg.
use strict;
use warnings;
use Text::ParseWords;
binmode(STDOUT, ":encoding(UTF-8)");

my $ABIB = shift @ARGV or die "Gebruik: perl $0 <ABIB> <doelmap>\n";
my $DEST = shift @ARGV or die "Gebruik: perl $0 <ABIB> <doelmap>\n";
my $CSV  = "tabellen/publicatie/NLCS_Query_Arceringen-concept-5.2.csv";
die "CSV niet gevonden: $CSV\n" unless -f $CSV;
mkdir $DEST unless -d $DEST;

my $S  = 60;      # viewBox-grootte (patrooneenheden)
my $MM = 40;      # fysieke afmeting in mm
my $PI = 3.14159265358979;
my $REPEATS = 8;  # ~aantal herhalingen van de fijnste lijnafstand in de swatch

sub trim { my $s = shift; $s //= ""; $s =~ s/^\s+|\s+$//g; return $s; }

open(my $in, "<:encoding(UTF-8)", $CSV) or die "$CSV: $!";
my $hl = <$in>; $hl =~ s/^\x{FEFF}//; $hl =~ s/\r?\n$//;
my @H = parse_line(",", 0, $hl);
my %HI; for (0..$#H) { $HI{trim($H[$_])} = $_ }
my ($CI_AB,$CI_FASE,$CI_ARC,$CI_SCH,$CI_VRKL) = @HI{qw(abibliotheek fase arcering schaal vrkl_lang)};

my ($made, $skipped_verv, $skipped_empty) = (0,0,0);
while (my $line = <$in>) {
  $line =~ s/\r?\n$//; next unless length $line && $line =~ /\S/;
  my @f = parse_line(",", 0, $line);
  next unless defined $f[$CI_AB] && trim($f[$CI_AB]) eq $ABIB;
  my $fase = trim($f[$CI_FASE] // "");
  my $name = trim($f[$CI_ARC] // "");
  next unless length $name;
  if ($fase eq "V" || $name =~ /^V-/) { $skipped_verv++; next; }   # vervallen weglaten
  my $scale = trim($f[$CI_SCH] // "1"); $scale = 1 if !$scale || $scale !~ /^[0-9.]+$/;
  my $vrkl = trim($f[$CI_VRKL] // "");
  if (!length $vrkl) { $skipped_empty++; }

  my @segs = render_families($vrkl, $scale);
  write_svg("$DEST/$name.svg", $name, \@segs);
  $made++;
}
close $in;

print "Doelmap : $DEST\n";
print "Gemaakt : $made SVG-swatches (abibliotheek $ABIB)\n";
print "Overgeslagen: $skipped_verv vervallen", ($skipped_empty ? ", $skipped_empty zonder patroon (leeg swatch)" : ""), "\n";

# -- lijnfamilies -> lijst SVG-<line>-strings, geclipt op de swatch --
# De schaal is adaptief: we normaliseren op de fijnste lijnafstand zodat er
# ~REPEATS herhalingen in de swatch passen (anders wordt een fijn patroon
# een onleesbare grijze massa).
sub render_families {
  my ($vrkl, $scale) = @_;
  my @out;
  return @out unless length $vrkl;
  my @fams = split /\s+/, $vrkl;

  # fijnste loodrechte afstand bepalen voor de normalisatie
  my $minsp = 0;
  for my $fam (@fams) {
    my @t = split /,/, $fam; next unless @t >= 5;
    my $sp = abs(($t[4] // 0) + 0);
    $minsp = $sp if $sp > 0.0001 && ($minsp == 0 || $sp < $minsp);
  }
  my $u = ($minsp > 0) ? ($S / $REPEATS) / $minsp : 1;   # eenheidsschaal

  for my $fam (@fams) {
    my @t = split /,/, $fam;
    next unless @t >= 5;
    my ($ang,$bx,$by,$dx,$dy) = map { $_ + 0 } @t[0..4];
    my @dash = map { $_ + 0 } @t[5..$#t];
    $dx *= $u; $dy *= $u;
    @dash = map { $_ * $u } @dash;
    my $spacing = abs($dy);
    my $ar = $ang * $PI / 180;
    my ($ux,$uy) = (cos($ar), sin($ar));       # lijnrichting
    my ($nx,$ny) = (-sin($ar), cos($ar));       # loodrecht
    my ($cx,$cy) = ($S/2, $S/2);
    my $L = 2*$S;                               # halve lijnlengte
    # dash-array (SVG: alle waarden positief; 0 -> stip)
    my $dasharr = "";
    if (@dash) {
      my @d = map { my $v = abs($_); $v = 0.4 if $v == 0; sprintf("%.4g",$v) } @dash;
      @d = (@d, @d) if @d % 2;                  # oneven -> verdubbelen voor nette herhaling
      $dasharr = join(" ", @d);
    }
    my $patlen = 0; $patlen += $_ for map { abs($_) } @dash;
    if ($spacing < 0.0001) {
      # geen loodrechte verspringing: teken één lijn door het midden
      push @out, seg_line($cx,$cy,$ux,$uy,$L,$dasharr,0);
      next;
    }
    my $K = int($L/$spacing) + 2;
    $K = 600 if $K > 600;                       # veiligheidscap
    for my $k (-$K .. $K) {
      my $px = $cx + $k*$spacing*$nx;
      my $py = $cy + $k*$spacing*$ny;
      my $off = ($patlen > 0) ? sprintf("%.4g", ($k*$dx) ) : 0;
      push @out, seg_line($px,$py,$ux,$uy,$L,$dasharr,$off);
    }
  }
  return @out;
}

sub seg_line {
  my ($px,$py,$ux,$uy,$L,$dasharr,$off) = @_;
  my ($x1,$y1) = ($px - $L*$ux, $py - $L*$uy);
  my ($x2,$y2) = ($px + $L*$ux, $py + $L*$uy);
  my $extra = "";
  $extra .= " stroke-dasharray=\"$dasharr\"" if length $dasharr;
  $extra .= " stroke-dashoffset=\"$off\""    if length $dasharr && $off ne "0";
  return sprintf('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f"%s/>', $x1,$y1,$x2,$y2,$extra);
}

sub write_svg {
  my ($path, $name, $segs) = @_;
  open(my $w, ">:encoding(UTF-8)", $path) or die "$path: $!";
  print $w qq{<svg xmlns="http://www.w3.org/2000/svg" width="${MM}mm" height="${MM}mm" viewBox="0 0 $S $S">\n};
  print $w qq{  <defs><clipPath id="c"><rect x="0" y="0" width="$S" height="$S"/></clipPath></defs>\n};
  print $w qq{  <rect x="0" y="0" width="$S" height="$S" fill="#fff" stroke="#bbb" stroke-width="0.5"/>\n};
  if (@$segs) {
    print $w qq{  <g clip-path="url(#c)" stroke="#111" stroke-width="0.5" fill="none">\n};
    print $w "    $_\n" for @$segs;
    print $w qq{  </g>\n};
  } else {
    print $w qq{  <text x="} . ($S/2) . qq{" y="} . ($S/2) . qq{" text-anchor="middle" font-family="sans-serif" font-size="4" fill="#999">geen patroon</text>\n};
  }
  print $w "</svg>\n";
  close $w;
}
