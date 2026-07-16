#!/usr/bin/perl
# Vergelijkt twee mappen met symbool-DWG's op NAAM en op INHOUD (MD5-hash).
# Categorieën:
#   - nieuw       : naam alleen in 5.2
#   - verwijderd  : naam alleen in 5.1
#   - gewijzigd   : zelfde naam, andere hash (inhoud veranderd)
#   - ongewijzigd : zelfde naam, zelfde hash
#
# Gebruik:  perl vergelijk_symbolen_hash.pl <map-5.1> <map-5.2> <out.html> [titel]
use strict;
use warnings;
use Digest::MD5;
use File::Find;
binmode(STDOUT, ":encoding(UTF-8)");

my ($D1, $D2, $OUT, $TITLE) = @ARGV;
die "Gebruik: perl $0 <map-5.1> <map-5.2> <out.html> [titel]\n" unless $D1 && $D2 && $OUT;
$TITLE //= "Symbolen-vergelijking 5.1 vs 5.2";

sub esc { my $s = shift // ''; $s =~ s/&/&amp;/g; $s =~ s/</&lt;/g; $s =~ s/>/&gt;/g; return $s; }

sub hashes {   # recursief (incl. submap zoals SKL/nieuw); sleutel = bestandsnaam zonder .dwg
  my $dir = shift; my %h;
  find(sub {
    return unless -f $_ && /\.dwg$/i;
    (my $name = $_) =~ s/\.dwg$//i;
    open(my $fh, "<:raw", $_) or return;
    $h{$name} = Digest::MD5->new->addfile($fh)->hexdigest;
    close $fh;
  }, $dir);
  return \%h;
}

my $h1 = hashes($D1);
my $h2 = hashes($D2);

my (@nieuw, @verwijderd, @gewijzigd, @ongewijzigd);
for my $n (sort keys %$h2) {
  if (!exists $h1->{$n})            { push @nieuw, $n }
  elsif ($h1->{$n} ne $h2->{$n})    { push @gewijzigd, $n }
  else                              { push @ongewijzigd, $n }
}
for my $n (sort keys %$h1) { push @verwijderd, $n unless exists $h2->{$n}; }

my $n1 = scalar keys %$h1;
my $n2 = scalar keys %$h2;

open(my $w, ">:encoding(UTF-8)", $OUT) or die "$OUT: $!";
print $w <<"HEAD";
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>@{[esc($TITLE)]}</title>
  <style>
    body { font-family: Arial, sans-serif; font-size: 13px; margin: 20px; color:#222; }
    h1 { font-size: 1.2em; color:#003865; }
    h2 { font-size: 1.05em; margin-top: 1.4em; border-bottom:1px solid #ccc; padding-bottom:3px; }
    .legend span { display:inline-block; padding:3px 10px; margin:2px 8px 2px 0; border-radius:3px; font-weight:600; }
    .b-nieuw{background:#d4edda;border:1px solid #b8dfc4;} .b-verw{background:#d0d0d0;border:1px solid #aaa;}
    .b-gew{background:#cce5ff;border:1px solid #99caff;} .b-ong{background:#f2f2f2;border:1px solid #ddd;}
    table{border-collapse:collapse;width:100%;margin-top:6px;} td,th{border:1px solid #ccc;padding:3px 8px;text-align:left;}
    th{background:#003865;color:#fff;} td.mono{font-family:Consolas,monospace;font-size:12px;}
    tr:nth-child(even) td{background:#fafafa;}
  </style>
</head>
<body>
  <h1>@{[esc($TITLE)]}</h1>
  <p>5.1: $n1 symbolen &nbsp;|&nbsp; 5.2: $n2 symbolen &nbsp;|&nbsp; vergelijking op bestandsnaam en MD5-hash van de DWG.</p>
  <div class="legend">
    <span class="b-nieuw">Nieuw in 5.2: @{[scalar @nieuw]}</span>
    <span class="b-verw">Verwijderd (was in 5.1): @{[scalar @verwijderd]}</span>
    <span class="b-gew">Gewijzigd (zelfde naam, andere inhoud): @{[scalar @gewijzigd]}</span>
    <span class="b-ong">Ongewijzigd: @{[scalar @ongewijzigd]}</span>
  </div>
HEAD

sub section {
  my ($title, $list, $cls) = @_;
  print $w "  <h2>$title (" . scalar(@$list) . ")</h2>\n";
  return print $w "  <p><em>geen</em></p>\n" unless @$list;
  print $w "  <table><thead><tr><th>#</th><th>symbool</th></tr></thead><tbody>\n";
  my $i = 0;
  for my $n (@$list) { $i++; print $w "    <tr><td>$i</td><td class=\"mono\">" . esc($n) . "</td></tr>\n"; }
  print $w "  </tbody></table>\n";
}

section("Gewijzigd &ndash; zelfde naam, andere hash", \@gewijzigd);
section("Nieuw in 5.2", \@nieuw);
section("Verwijderd (was in 5.1)", \@verwijderd);

print $w "  <h2>Ongewijzigd (" . scalar(@ongewijzigd) . ")</h2>\n  <p>Identieke naam én hash; niet uitgelijst.</p>\n";
print $w "</body>\n</html>\n";
close $w;

print "5.1-map : $D1 ($n1)\n5.2-map : $D2 ($n2)\n";
print "nieuw: ", scalar @nieuw, " | verwijderd: ", scalar @verwijderd,
      " | gewijzigd: ", scalar @gewijzigd, " | ongewijzigd: ", scalar @ongewijzigd, "\n";
print "WROTE $OUT\n";
