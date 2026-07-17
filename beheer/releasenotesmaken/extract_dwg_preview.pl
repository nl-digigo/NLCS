#!/usr/bin/perl
# Haalt de ingebedde preview-thumbnail uit DWG-bestanden (zoals de Windows
# Verkenner toont) en schrijft die als PNG (code 6) of BMP (code 2) naar een map.
#
# Gebruik:  perl extract_dwg_preview.pl <dwg-map> <preview-doelmap>
#
# DWG-preview-sectie: op offset 0x0D staat een 4-byte pointer naar de image-
# sectie; daar volgt een 16-byte sentinel, 4-byte grootte, 1-byte aantal beelden
# en per beeld 1-byte code + 4-byte (absolute) start + 4-byte grootte.
#   code 2 = BMP (DIB zonder BITMAPFILEHEADER)   code 6 = PNG (direct bruikbaar)
use strict;
use warnings;
use File::Find;

my ($DWGDIR, $OUT) = @ARGV;
die "Gebruik: perl $0 <dwg-map> <preview-doelmap>\n" unless $DWGDIR && $OUT;
mkdir $OUT unless -d $OUT;

# recursief alle dwg's verzamelen (incl. submap zoals SKL/nieuw)
my @paths;
find(sub { push @paths, $File::Find::name if -f $_ && /\.dwg$/i }, $DWGDIR);
my @dwg = sort @paths;

my ($png,$bmp,$none,$err) = (0,0,0,0);
for my $f (@dwg) {
  (my $stem = $f) =~ s#.*/##; $stem =~ s/\.dwg$//i;
  open(my $fh, "<:raw", $f) or do { $err++; next };
  local $/; my $d = <$fh>; close $fh;
  next if length($d) < 0x11;
  my $off = unpack("V", substr($d, 0x0D, 4));
  next if $off <= 0 || $off + 21 > length($d);
  my $cnt = unpack("C", substr($d, $off + 20, 1));
  my $wrote = 0;
  for my $i (0 .. $cnt - 1) {
    my $p = $off + 21 + $i * 9;
    last if $p + 9 > length($d);
    my $code = unpack("C", substr($d, $p, 1));
    my ($start, $size) = unpack("VV", substr($d, $p + 1, 8));
    next unless $size > 0 && $start > 0 && $start + $size <= length($d);
    my $img = substr($d, $start, $size);
    if ($code == 6) {                       # PNG
      write_bin("$OUT/$stem.png", $img); $png++; $wrote = 1; last;
    } elsif ($code == 2) {                   # BMP (DIB -> voeg fileheader toe)
      write_bin("$OUT/$stem.bmp", dib_to_bmp($img)); $bmp++; $wrote = 1; last;
    }
  }
  $none++ unless $wrote;
}

print "DWG's: ", scalar(@dwg), " | preview PNG: $png | preview BMP: $bmp | zonder preview: $none",
      ($err ? " | leesfouten: $err" : ""), "\n";
print "doelmap: $OUT\n";

sub write_bin { my ($path,$data)=@_; open(my $w,">:raw",$path) or die "$path: $!"; print $w $data; close $w; }

sub dib_to_bmp {
  my $dib = shift;
  my $biSize   = unpack("V", substr($dib, 0, 4));
  my $biBits   = unpack("v", substr($dib, 14, 2));
  my $biClrUsed= length($dib) >= 36 ? unpack("V", substr($dib, 32, 4)) : 0;
  my $palette  = 0;
  if ($biBits <= 8) { my $n = $biClrUsed ? $biClrUsed : (1 << $biBits); $palette = $n * 4; }
  my $pixoff = 14 + $biSize + $palette;
  my $filesize = 14 + length($dib);
  my $hdr = "BM" . pack("V", $filesize) . pack("vv", 0, 0) . pack("V", $pixoff);
  return $hdr . $dib;
}
