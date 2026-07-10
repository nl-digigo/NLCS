#!/usr/bin/env perl
#
# Genereert een HTML-overzicht van NLCS-symbolen, hiërarchisch gegroepeerd op
# zoekfilter. Elk symbool deelt de hoofdgroep (bv. SKL); daarna komt er per
# niveau een term bij (SKL -> SKL-DATA -> SKL-DATA_GLASVEZEL -> ...). Gelijke
# filterniveaus worden met rowspan samengevoegd, zodat symbolen op het meest
# uitgebreide gedeelde filter bij elkaar staan.
#
# V- en B-prefixes worden voor de groepering genegeerd (die horen bij hetzelfde
# zoekfilter); ze verschijnen wel als aparte varianten. Bestaande en nieuwe
# symbolen krijgen een eigen kleur.
#
# Gebruik:
#   perl zoekfilter_overzicht.pl <dwg-bestaand-map> <dwg-nieuw-map> <svg-map> <out.html> [titel]
#
use strict;
use warnings;

my ($dwg_best, $dwg_new, $svgdir, $out, $title) = @ARGV;
die "Gebruik: perl $0 <dwg-bestaand> <dwg-nieuw> <svg-map> <out.html> [titel]\n"
    unless $dwg_best && $dwg_new && $svgdir && $out;
$title //= "Zoekfilter-overzicht";

sub esc { my $s = shift // ''; $s =~ s/&/&amp;/g; $s =~ s/</&lt;/g; $s =~ s/>/&gt;/g; $s =~ s/"/&quot;/g; return $s; }

# --- bestanden verzamelen ---
my @files;
sub collect {
    my ($dir, $status) = @_;
    opendir(my $dh, $dir) or return;
    for my $f (sort readdir $dh) {
        next unless $f =~ /\.dwg$/i;
        push @files, { fname => $f, status => $status };
    }
    closedir $dh;
}
collect($dwg_best, 'bestaand');
collect($dwg_new,  'nieuw');
die "Geen DWG-bestanden gevonden.\n" unless @files;

# --- boom opbouwen ---
my $root = { children => {}, order => [], symbols => [], depth => 0, parent => undef };
my $maxdepth = 0;

for my $e (@files) {
    my $stem = $e->{fname}; $stem =~ s/\.dwg$//i;
    my $variant = '';
    my $core = $stem;
    if ($core =~ /^([BV])-(.+)$/) { $variant = $1; $core = $2; }

    # tokens: hoofdgroep vóór eerste '-', daarna op '_' gesplitst; -SO-suffix negeren
    my $tokcore = $core;
    $tokcore =~ s/-SO$//;
    my @toks;
    if ($tokcore =~ /^([A-Z0-9]+)-(.+)$/) {
        @toks = ($1, split(/_/, $2));
    } else {
        @toks = ($tokcore);
    }
    my $code = $toks[0];

    my @cum;
    $cum[0] = $code;
    for (my $i = 1; $i < @toks; $i++) {
        $cum[$i] = "$code-" . join('_', @toks[1..$i]);
    }
    $maxdepth = @toks if @toks > $maxdepth;

    my $node = $root;
    for (my $i = 0; $i < @toks; $i++) {
        my $t = $toks[$i];
        if (!exists $node->{children}{$t}) {
            $node->{children}{$t} = {
                children => {}, order => [], symbols => [],
                depth => $i + 1, filter => $cum[$i], token => $t, parent => $node,
            };
            push @{$node->{order}}, $t;
        }
        $node = $node->{children}{$t};
    }
    push @{$node->{symbols}}, { stem => $stem, variant => $variant, status => $e->{status} };
}

# --- hulpfuncties ---
my %subcache;
sub subrows {
    my $n = shift;
    return $subcache{"$n"} if exists $subcache{"$n"};
    my $c = scalar @{$n->{symbols}};
    $c += subrows($n->{children}{$_}) for @{$n->{order}};
    return $subcache{"$n"} = $c;
}

my %vord = ('' => 0, 'B' => 1, 'V' => 2);
my @rows;
sub walk {
    my ($n) = @_;
    for my $s (sort { ($vord{$a->{variant}} <=> $vord{$b->{variant}}) || ($a->{stem} cmp $b->{stem}) } @{$n->{symbols}}) {
        push @rows, { node => $n, sym => $s };
    }
    walk($n->{children}{$_}) for (sort @{$n->{order}});
}
walk($root);

my $n_best = grep { $_->{status} eq 'bestaand' } @files;
my $n_new  = grep { $_->{status} eq 'nieuw' } @files;

# --- SVG aanwezig? ---
sub svg_exists { my $name = shift; return -f "$svgdir/$name"; }

# --- HTML schrijven ---
open(my $fh, '>:encoding(UTF-8)', $out) or die "Kan niet schrijven: $out ($!)\n";

my @heads;
push @heads, "<th>Niveau 1</th>";
push @heads, "<th>Niveau $_</th>" for (2..$maxdepth);
my $hierhead = join('', @heads);

print $fh <<HEAD;
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@{[esc($title)]}</title>
<style>
  body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; margin: 2em; color: #222; }
  h1 { border-bottom: 2px solid #003865; padding-bottom: .3em; color: #003865; }
  .info { color: #555; font-size: 14px; margin: .3em 0 1em; }
  .legend { margin: 1em 0 1.5em; font-size: 14px; }
  .legend span { display: inline-block; padding: 3px 12px; border-radius: 12px; margin-right: 10px; font-weight: 600; }
  .badge-nieuw    { background: #e6f4ea; color: #137333; border: 1px solid #a8d5b5; }
  .badge-bestaand { background: #eef1f5; color: #3c4043; border: 1px solid #cbd2da; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; }
  th, td { border: 1px solid #d7dce2; padding: 6px 10px; text-align: left; vertical-align: top; }
  thead th { background: #003865; color: #fff; position: sticky; top: 0; z-index: 2; }
  td.hier, td.lvl1 { font-family: Consolas, monospace; background: #f7f9fb; color: #003865;
                     white-space: nowrap; font-weight: 600; }
  td.lvl1 { background: #eaf0f6; }
  td.empty { background: #fcfdfe; border-left: 1px dashed #e3e8ee; }
  td.name { font-family: Consolas, monospace; white-space: nowrap; }
  td.img { text-align: center; }
  td.img img { max-width: 90px; max-height: 90px; min-width: 24px; min-height: 24px; }
  td.status { text-align: center; font-weight: 600; white-space: nowrap; }
  /* statuskleuren op de symboolrijen */
  .nieuw    { background: #e9f7ee; }
  .bestaand { background: #ffffff; }
  td.status.nieuw    { color: #137333; }
  td.status.bestaand { color: #5f6368; }
  tr:hover .nieuw    { background: #d8f0e1; }
  tr:hover .bestaand { background: #f2f5f8; }
  .missing { color: #c00; font-style: italic; }
</style>
</head>
<body>
<h1>@{[esc($title)]}</h1>
<p class="info">@{[scalar @files]} symbolen — hiërarchisch gegroepeerd op zoekfilter (V-/B-varianten genegeerd voor groepering)</p>
<div class="legend">
  <span class="badge-nieuw">nieuw: $n_new</span>
  <span class="badge-bestaand">bestaand (5.0): $n_best</span>
</div>
<table>
<thead><tr>$hierhead<th>Symbool (bestand)</th><th>Afbeelding</th><th>Status</th></tr></thead>
<tbody>
HEAD

my %emitted;
for my $r (@rows) {
    my @chain;
    my $n = $r->{node};
    while ($n && $n->{depth} >= 1) { unshift @chain, $n; $n = $n->{parent}; }
    my $plen = scalar @chain;

    print $fh "<tr>";
    for (my $lvl = 1; $lvl <= $maxdepth; $lvl++) {
        if ($lvl <= $plen) {
            my $node = $chain[$lvl - 1];
            if (!$emitted{"$node"}) {
                $emitted{"$node"} = 1;
                my $rs  = subrows($node);
                my $cls = ($lvl == 1) ? 'lvl1' : 'hier';
                print $fh "<td class=\"$cls\" rowspan=\"$rs\">@{[esc($node->{filter})]}</td>";
            }
        } else {
            print $fh "<td class=\"empty\"></td>";
        }
    }
    my $s   = $r->{sym};
    my $cls = $s->{status};
    my $svg = "$s->{stem}.svg";
    my $src = $svg; $src =~ s/ /%20/g;
    my $img = svg_exists($svg)
        ? "<img src=\"@{[esc($src)]}\" alt=\"\" loading=\"lazy\">"
        : "<span class=\"missing\">geen svg</span>";
    print $fh "<td class=\"name $cls\">@{[esc($s->{stem})]}</td>";
    print $fh "<td class=\"img $cls\">$img</td>";
    print $fh "<td class=\"status $cls\">$s->{status}</td>";
    print $fh "</tr>\n";
}

print $fh "</tbody></table>\n</body></html>\n";
close $fh;

print "geschreven: $out\n";
print "symbolen:   @{[scalar @files]} (nieuw: $n_new, bestaand: $n_best)\n";
print "kolommen:   $maxdepth filterniveaus\n";
