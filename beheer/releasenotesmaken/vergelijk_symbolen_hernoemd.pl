#!/usr/bin/perl
# Omgekeerde vergelijking: match op INHOUD (MD5-hash), rapporteer symbolen met
# DEZELFDE inhoud maar een ANDERE naam tussen 5.1 en 5.2 -> hernoemd.
#
# Gebruik:  perl vergelijk_symbolen_hernoemd.pl <map-5.1> <map-5.2> <out.html> [titel]
use strict;
use warnings;
use Digest::MD5;
use File::Find;
binmode(STDOUT, ":encoding(UTF-8)");

my ($D1, $D2, $OUT, $TITLE) = @ARGV;
die "Gebruik: perl $0 <map-5.1> <map-5.2> <out.html> [titel]\n" unless $D1 && $D2 && $OUT;
$TITLE //= "Symbolen hernoemd 5.1 -> 5.2 (zelfde inhoud, andere naam)";

sub esc { my $s = shift // ''; $s =~ s/&/&amp;/g; $s =~ s/</&lt;/g; $s =~ s/>/&gt;/g; return $s; }

sub byhash {   # recursief; md5 -> { naam => 1 }
  my $dir = shift; my %h;
  find(sub {
    return unless -f $_ && /\.dwg$/i;
    (my $name = $_) =~ s/\.dwg$//i;
    open(my $fh, "<:raw", $_) or return;
    my $md5 = Digest::MD5->new->addfile($fh)->hexdigest; close $fh;
    $h{$md5}{$name} = 1;
  }, $dir);
  return \%h;
}

my $h1 = byhash($D1);
my $h2 = byhash($D2);

# per gedeelde hash: namen die alleen in 5.1 resp. alleen in 5.2 voorkomen
my @rename;
for my $md5 (sort keys %$h2) {
  next unless exists $h1->{$md5};
  my @old = sort grep { !$h2->{$md5}{$_} } keys %{$h1->{$md5}};
  my @new = sort grep { !$h1->{$md5}{$_} } keys %{$h2->{$md5}};
  next unless @old && @new;   # inhoud met in beide releases een naam die verschilt
  push @rename, { md5 => $md5, old => \@old, new => \@new };
}

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
    p.info{color:#555;}
    table{border-collapse:collapse;width:100%;margin-top:8px;} td,th{border:1px solid #ccc;padding:4px 8px;text-align:left;vertical-align:top;}
    th{background:#003865;color:#fff;} td.mono{font-family:Consolas,monospace;font-size:12px;}
    td.old{background:#f6e0e0;} td.new{background:#e0f0e0;}
    tr:hover td{background:#eef3f8;}
  </style>
</head>
<body>
  <h1>@{[esc($TITLE)]}</h1>
  <p class="info">Match op MD5-hash van de DWG. Getoond: inhoud die in beide releases voorkomt maar met een andere bestandsnaam &rarr; @{[scalar @rename]} hernoemingen.</p>
  <table><thead><tr><th>#</th><th>5.1 (oude naam)</th><th>5.2 (nieuwe naam)</th></tr></thead><tbody>
HEAD

my $i = 0;
for my $r (sort { $a->{old}[0] cmp $b->{old}[0] } @rename) {
  $i++;
  print $w "    <tr><td>$i</td><td class=\"mono old\">" . esc(join("<br>", @{$r->{old}}))
         . "</td><td class=\"mono new\">" . esc(join("<br>", @{$r->{new}})) . "</td></tr>\n";
}
print $w "  </tbody></table>\n</body>\n</html>\n";
close $w;

print "hernoemingen (zelfde hash, andere naam): ", scalar @rename, "\n";
print "WROTE $OUT\n";
for my $r (@rename[0 .. ($#rename < 14 ? $#rename : 14)]) {
  print "  ", join(",", @{$r->{old}}), "  ->  ", join(",", @{$r->{new}}), "\n";
}
