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
# Gebruik (twee modi):
#   1) losse mappen bestaand/nieuw:
#      perl zoekfilter_overzicht.pl <dwg-bestaand-map> <dwg-nieuw-map> <svg-map> <out.html> [titel]
#   2) referentievergelijking (5.2 vs 5.0): classificeert per bestandsnaam
#      perl zoekfilter_overzicht.pl --ref <dwg-5.2-map> <dwg-5.0-ref-map> <svg-map> <out.html> [titel]
#
use strict;
use warnings;

sub esc { my $s = shift // ''; $s =~ s/&/&amp;/g; $s =~ s/</&lt;/g; $s =~ s/>/&gt;/g; $s =~ s/"/&quot;/g; return $s; }

sub list_dwg {
    my $dir = shift;
    my @out;
    opendir(my $dh, $dir) or return @out;
    for my $f (sort readdir $dh) { push @out, $f if $f =~ /\.dwg$/i; }
    closedir $dh;
    return @out;
}

my @files;
my ($svgdir, $out, $title);

# optionele objecttabel: --obj <csv>  (vergelijk zoekfilters met kolom 'sobject')
my $objcsv;
{
    my @a = @ARGV;
    for (my $i = 0; $i < @a; $i++) {
        if ($a[$i] eq '--obj') { $objcsv = $a[$i + 1]; splice(@a, $i, 2); last; }
    }
    @ARGV = @a;
}

# sobject-set laden (scheidingsteken per bestand detecteren, kolom op naam zoeken)
my %sobject;
my $have_obj = 0;
if (defined $objcsv && -f $objcsv) {
    open(my $oh, '<:encoding(UTF-8)', $objcsv) or die "Kan objecttabel niet lezen: $objcsv\n";
    my $hdr = <$oh>;
    $hdr //= '';
    $hdr =~ s/^\x{FEFF}//;      # BOM
    $hdr =~ s/[\r\n]+$//;
    my $sep = (($hdr =~ tr/;//) >= ($hdr =~ tr/,//)) ? ';' : ',';
    my @cols = split /\Q$sep\E/, $hdr, -1;
    my $idx = -1;
    for my $i (0 .. $#cols) { if (lc($cols[$i]) eq 'sobject') { $idx = $i; last; } }
    if ($idx >= 0) {
        while (my $line = <$oh>) {
            $line =~ s/[\r\n]+$//;
            my @f = split /\Q$sep\E/, $line, -1;
            my $v = $f[$idx];
            next unless defined $v && $v ne '';
            $v =~ s/^\s+|\s+$//g;
            $sobject{$v} = 1 if $v ne '';
        }
        $have_obj = 1;
    }
    close $oh;
}

if (@ARGV && $ARGV[0] eq '--ref') {
    my ($mode, $dwg52, $ref50);
    ($mode, $dwg52, $ref50, $svgdir, $out, $title) = @ARGV;
    die "Gebruik: perl $0 --ref <dwg-5.2> <dwg-5.0-ref> <svg-map> <out.html> [titel]\n"
        unless $dwg52 && $ref50 && $svgdir && $out;
    my %in50 = map { $_ => 1 } list_dwg($ref50);
    for my $f (list_dwg($dwg52)) {
        push @files, { fname => $f, status => ($in50{$f} ? 'bestaand' : 'nieuw') };
    }
} else {
    my ($dwg_best, $dwg_new);
    ($dwg_best, $dwg_new, $svgdir, $out, $title) = @ARGV;
    die "Gebruik: perl $0 <dwg-bestaand> <dwg-nieuw> <svg-map> <out.html> [titel]\n"
        unless $dwg_best && $dwg_new && $svgdir && $out;
    push @files, { fname => $_, status => 'bestaand' } for list_dwg($dwg_best);
    push @files, { fname => $_, status => 'nieuw' }    for list_dwg($dwg_new);
}
$title //= "Zoekfilter-overzicht";
die "Geen DWG-bestanden gevonden.\n" unless @files;

# --- boom opbouwen ---
my $root = { children => {}, order => [], symbols => [], depth => 0, parent => undef };
my $maxdepth = 0;

for my $e (@files) {
    my $stem = $e->{fname}; $stem =~ s/\.dwg$//i;
    my $variant = '';
    my $core = $stem;
    if ($core =~ /^([BV])-(.+)$/) { $variant = $1; $core = $2; }

    # tokens: hoofdgroep vóór eerste '-'; het objectpad (met '_' als scheiding)
    # is het deel daarna tót het volgende '-'. Het element-/bewerkingssuffix
    # (bv. -SO, -D, -G, -P) staat achter dat streepje en hoort niet bij de
    # zoekfilter, dus dat kappen we af.
    my @toks;
    if ($core =~ /^([A-Z0-9]+)-(.+)$/) {
        my ($code0, $rest) = ($1, $2);
        (my $objpath = $rest) =~ s/-.*$//;
        @toks = ($code0, split(/_/, $objpath));
    } else {
        @toks = ($core);
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

# subtreeHit: staat deze zoekfilter, of een gedetailleerder niveau eronder,
# in de sobject-kolom? Zo ja, dan hoeft (dit én) een minder uitgebreid
# bovenliggend niveau niet rood.
my %hitcache;
sub subtreeHit {
    my $n = shift;
    return $hitcache{"$n"} if exists $hitcache{"$n"};
    my $hit = ($n->{filter} && $sobject{ $n->{filter} }) ? 1 : 0;
    if (!$hit) {
        for my $t (@{$n->{order}}) {
            if (subtreeHit($n->{children}{$t})) { $hit = 1; last; }
        }
    }
    return $hitcache{"$n"} = $hit;
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
my $obj_legend = $have_obj
    ? '  <span class="badge-insob">groen zoekfilter = staat in kolom sobject</span>' . "\n"
    . '  <span class="badge-notin">rood zoekfilter = niet in sobject (ook niet dieper)</span>'
    : '';

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
  .badge-notin    { background: #f9d2d2; color: #a11; border: 1px solid #e2a3a3; }
  .badge-insob    { background: #cdeccf; color: #14612a; border: 1px solid #9fcfa6; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; }
  th, td { border: 1px solid #d7dce2; padding: 6px 10px; text-align: left; vertical-align: top; }
  thead th { background: #003865; color: #fff; position: sticky; top: 0; z-index: 2; }
  td.hier, td.lvl1 { font-family: Consolas, monospace; background: #f7f9fb; color: #003865;
                     white-space: nowrap; font-weight: 600; }
  td.lvl1 { background: #eaf0f6; }
  /* zoekfilter komt niet voor in kolom 'sobject' van de objecttabel */
  td.hier.notin, td.lvl1.notin { background: #f9d2d2; color: #a11; }
  /* zoekfilter staat zelf in kolom 'sobject' */
  td.hier.insob, td.lvl1.insob { background: #cdeccf; color: #14612a; }
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
$obj_legend
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
                if ($have_obj) {
                    if ($node->{filter} && $sobject{ $node->{filter} }) {
                        $cls .= ' insob';       # term zelf gevonden -> groen
                    } elsif (!subtreeHit($node)) {
                        $cls .= ' notin';       # nergens in subtak gevonden -> rood
                    }
                }
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
