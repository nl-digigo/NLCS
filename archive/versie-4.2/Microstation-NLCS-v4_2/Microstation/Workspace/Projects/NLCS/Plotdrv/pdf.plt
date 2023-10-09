;======================================================================
;
;  Bentley Adobe PDF Printer Driver Configuration File
;
;  $RCSfile: pdf.plt,v $
;  $Revision: 1.66.2.2 $  $Date: 2006/10/31 19:34:19 $
;
;  Printer driver configuration files are stored in two directories:
;
;    $(_USTN_WORKSPACEROOT)/System/plotdrv/
;    $(_USTN_WORKSPACEROOT)/Standards/plotdrv/
;
;  System/plotdrv/ should be reserved for printer driver configuration
;  files delivered by MicroStation and other Bentley products.
;  Standards/plotdrv/ is provided as a place for you to store
;  customized versions of these files. For simplicity, you may choose
;  to store frequently-used files in Standards/plotdrv/ even if you do
;  not customize them.
;
;  To minimize the risk of losing your changes during a product
;  reinstallation, do not edit the files in the System/plotdrv/
;  directory. Instead, copy the necessary files to Standards/plotdrv/
;  and edit them there. If the printer driver configuration file
;  depends on other files, such as PostScript prolog (*.pro) files,
;  copy them to the same directory.
;
;  NOTE: With the introduction of the Printer Driver Configuration
;        Editor in MicroStation 8.9.3, the .plt printer driver
;        configuration file format has been superseded by the XML-based
;        .pltcfg format. MicroStation continues to support legacy .plt
;        files, but migration to .pltcfg files is encouraged.
;
;======================================================================

;----------------------------------------------------------------------
; The lines in this section are required for proper operation.
; This section should appear before any other records in the file.
driver = pdf
model = mdl
num_pens = 255
;----------------------------------------------------------------------

; Default extension for PDF plot files.
default_extension = "pdf"

; Refer to the documentation for available default_outFile qualifiers, such as /auto_overwrite
; To plot to a TCP/IP address using LPR, use the syntax default_outFile = xxx.xxx.xxx.xxx
default_outFile = "$(parentdevdir_(_DGNFILE))\$(MS_PLTMODELNAME).pdf"

; Uncomment the record below to instruct MicroStation to open the PDF
; file in your PDF viewer immediately after creating the file.
; The "ShellExecute" command is a reserved keyword indicating that
; MicroStation should open the plot file using whatever Windows
; application has registered the plot file extension.
;program /post /command="ShellExecute"

; Color mode options are color, grayscale, or monochrome
color_mode = color

; If true, RGB raster is converted to a color palette when possible.
; Note that this generally results in smaller plot files, at the
; expense of plot processing time and memory requirements.
optimize_raster_color_depth = true

; If point_size is set to zero, pattern points are not printed.
; If the size is non-zero, pattern points are printed using diameters calculated from their weights.
point_size = 0.01;

; Automatically center plot on page
autocenter

; Refer to the documentation for available border qualifiers.
;border /filename /time /text_height=0.35

; Substitute the name of a pen table file to be automatically attached when this printer
; driver configuration is loaded.  If set to "0", any currently attached pen table will
; be automatically detached when this printer configuration is loaded.
;pentable = "C:\Pen Table Directory\My Pen Table.tbl"

; If the record below is uncommented, the print dialog's "Plot to 3D" toggle
; will be turned on automatically when the PDF driver is loaded.
;plot_to_3d

; To improve performance plotting large, detailed designs,
; you can lower the PDF resolution from the default 600 dpi.
;resolution(in)  = (0.001666666666666666666667, 0.001666666666666666666667) ; 600 dpi
;resolution(in) = (0.003333333333333333333333, 0.003333333333333333333333) ; 300 dpi
;resolution(in) = (0.005,                      0.005)                      ; 200 dpi
resolution(in) = (0.006666666666666666666667, 0.006666666666666666666667) ; 150 dpi

; ISO size records

size=(297,210)  /units=mm /penScale=1.0 /name="ISO A4"
size=(420,297)  /units=mm /penScale=1.0  /name="ISO A3  (297x420)"  
size=(594,297)  /units=mm /penScale=1.0  /name="ISO A3  (297x594)"  
size=(841,297)  /units=mm /penScale=1.0  /name="ISO A3  (297x841)"      
size=(1050,297)  /units=mm /penScale=1.0 /name="ISO A3  (297x1050)"     
size=(1189,297)  /units=mm /penScale=1.0 /name="ISO A3  (297x1189)"     
size=(1260,297)  /units=mm /penScale=1.0 /name="ISO A3  (297x1260)"     
size=(1470,297)  /units=mm /penScale=1.0 /name="ISO A3  (297x1470)" 
size=(1680,297)  /units=mm /penScale=1.0 /name="ISO A3  (297x1680)" 
size=(1890,297)  /units=mm /penScale=1.0 /name="ISO A3  (297x1890)" 
size=(2100,297)  /units=mm /penScale=1.0 /name="ISO A3  (297x2100)" 
size=(594,420)  /units=mm /penScale=1.0  /name="ISO A2 (420x594)"
size=(630,420)  /units=mm /penScale=1.0  /name="ISO A2 (420x630)"   
size=(841,420)  /units=mm /penScale=1.0  /name="ISO A2 (420x841)"   
size=(1050,420)  /units=mm /penScale=1.0 /name="ISO A2 (420x1050)"  
size=(1189,420)  /units=mm /penScale=1.0 /name="ISO A2 (420x1189)"  
size=(1260,420)  /units=mm /penScale=1.0 /name="ISO A2 (420x1260)"  
size=(1470,420)  /units=mm /penScale=1.0 /name="ISO A2 (420x1470)"  
size=(1680,420)  /units=mm /penScale=1.0 /name="ISO A2 (420x1680)"  
size=(1890,420)  /units=mm /penScale=1.0 /name="ISO A2 (420x1890)"  
size=(2100,420)  /units=mm /penScale=1.0 /name="ISO A2 (420x2100)" 
size=(630,594)  /units=mm /penScale=1.0  /name="ISO A1 (594x630)"
size=(841,594)  /units=mm /penScale=1.0  /name="ISO A1 (594x841)"
size=(1050,594)  /units=mm /penScale=1.0 /name="ISO A1 (594x1050)"
size=(1189,594)  /units=mm /penScale=1.0 /name="ISO A1 (594x1189)"
size=(1260,594)  /units=mm /penScale=1.0 /name="ISO A1 (594x1260)"
size=(1470,594)  /units=mm /penScale=1.0 /name="ISO A1 (594x1470)"
size=(1680,594)  /units=mm /penScale=1.0 /name="ISO A1 (594x1680)"
size=(1890,594)  /units=mm /penScale=1.0 /name="ISO A1 (594x1890)"
size=(2100,594)  /units=mm /penScale=1.0 /name="ISO A1 (594x2100)"
size=(840,841) /units=mm /penScale=1.0  /name="ISO A0 (841x840)"
size=(1050,841) /units=mm /penScale=1.0 /name="ISO A0 (841x1050)"
size=(1189,841) /units=mm /penScale=1.0 /name="ISO A0 (841x1189)"
size=(1260,841) /units=mm /penScale=1.0 /name="ISO A0 (841x1260)"
size=(1470,841) /units=mm /penScale=1.0 /name="ISO A0 (841x1470)"
size=(1680,841) /units=mm /penScale=1.0 /name="ISO A0 (841x1680)"
size=(1890,841) /units=mm /penScale=1.0 /name="ISO A0 (841x1890)"
size=(2100,841) /units=mm /penScale=1.0 /name="ISO A0 (841x2100)"

; Pen 0 is the 'background' pen.  Other pens get their color by default from
; the corresponding color in the current design file color table.  The background
; pen instead defaults to white.  To have the background pen get its value from
; the master file color table, you can assign it an RGB of (-1, -1, -1).
;pen(0)=/rgb=(-1, -1, -1)

;---------------------------------------------------------------------------------
; The style records below define how design file cosmetic line styles
; are plotted in paper units.  Values indicate pen down/up distances.
; For example, the (0.35, 1.05) pattern leaves the pen down for 0.35
; units and up for 1.05 units.  Valid units are MM, IN, or DOTS.
; If not specified, the units are assumed to be DOTS.

style(1) = (0.35, 1.05)                         /nohardware  /units=mm ; dot
style(2) = (1.75, 1.05)                         /nohardware  /units=mm ; med dash
style(3) = (4.20, 1.40)                         /nohardware  /units=mm ; long dash
style(4) = (2.80, 1.05, 0.70, 1.05)             /nohardware  /units=mm ; dot-dash
style(5) = (1.40, 1.40)                         /nohardware  /units=mm ; short dash
style(6) = (2.10, 0.70, 0.70, 0.70, 0.70, 0.70) /nohardware  /units=mm ; dash-dot-dot
style(7) = (2.80, 0.70, 1.40, 0.70)             /nohardware  /units=mm ; long dash - short dash
;---------------------------------------------------------------------------------

default_linecap  = flat  ; values: flat, round, square
default_linejoin = round ; values: miter, round, bevel

; Clip miter line joins to bevels at angles sharper than this angle.
; Range 45-180 (in degrees). Smaller values result in longer spikes.
max_miter_angle = 90

; Specify the mapping of MicroStation line weights to line thickness on paper.
; Units are MM, IN, or DOTS (the default if not otherwise specified)                    
weight_strokes(mm)=(0.01,0.18,0.25,0.35,0.5,0.7,1,1.2,1.3,1.4,1.5,1.6,1.65, \
                    1.70,1.75,1.80,1.85,1.90,1.95,2.0,2.1,2.2,2.3,2.4,2.5,  \
                    2.6,2.7,2.8,2.9,3.0,3.1) 



; The following record controls printing of Raster Manager and 87/88 image data.
raster_parameters /quality=50 /contrast=0 /brightness=0 /grayscale=0

; The following record controls the quality of rasterized plots.
; The range is 0 < quality <= 100. The default is 100, which means plots
; are rasterized at full device resolution. Smaller values may be used to
; reduce rasterized plot file size.
; rasterized_parameters /quality=100

;=======================================================================
; The command records below are specific to the PDF driver.
;=======================================================================

;------------------------------------------------------------------------------
; Turn the book marks on and off.  On by default.
; CmdName /appname="pdf" /command="BookMarks" /qualifier="On"
CmdName /appname="pdf" /command="BookMarks" /qualifier="Off"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Turn the Level/File optional content on and off.  Off by default.
; CmdName /appname="pdf" /command="EnableOptionalContent" /qualifier="On"
CmdName /appname="pdf" /command="EnableOptionalContent" /qualifier="Off"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Control how Level/File optional content is printed.  "AsDisplayed" by default.
; Changing to "AsCreated" allows users to turn on/off levels and references for
; display purpose, but forces all printouts to use the original display states.
CmdName /appname="pdf" /command="PrintOptionalContent" /qualifier="AsDisplayed"
;CmdName /appname="pdf" /command="PrintOptionalContent" /qualifier="AsCreated"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Specify what is used for the optional content level labels: level display
; names (formatted by MS_LEVEL_DISPLAY_FORMAT), unformatted level names,
; or level descriptions.
CmdName /appname="pdf" /command="LevelLabel" /qualifier="DisplayName"
;CmdName /appname="pdf" /command="LevelLabel" /qualifier="Name"
;CmdName /appname="pdf" /command="LevelLabel" /qualifier="Description"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Turn engineering links on and off.  On by default.
CmdName /appname="pdf" /command="EngineeringLinks" /qualifier="On"
;CmdName /appname="pdf" /command="EngineeringLinks" /qualifier="Off"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Select the version of PDF that will be created.  PDF 1.5 by default.
CmdName /appname="pdf" /command="Version" /qualifier="Acrobat 7 (PDF 1.6)"
;CmdName /appname="pdf" /command="Version" /qualifier="Acrobat 6 (PDF 1.5)"
;CmdName /appname="pdf" /command="Version" /qualifier="Acrobat 6 (PDF 1.5)/Viewable in Acrobat 5"
;CmdName /appname="pdf" /command="Version" /qualifier="Acrobat 5 (PDF 1.4)"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Uncomment the CmdName line below and change the qualifier to your owner
; password if you wish to protect the output PDF file.  Note that if this
; password is set, you not be able to change the PDF file permissions without
; specifying it.  If the user password is defined, but not the owner password,
; the user password will be used for the owner password also.
;CmdName /appname="pdf" /command="OwnerPassword" /qualifier="my_owner_password"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Uncomment the CmdName line below and change the qualifier to your user
; password if you wish to protect the output PDF file.  Note that if this
; password is set, you will not be able to open or view the PDF file without
; specifying it.
;CmdName /appname="pdf" /command="UserPassword" /qualifier="my_user_password"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Control printing permissions. Default qualifier is "1". Legal values are:
; 0 = Do not allow printing
; 1 = Allow high resolution printing
; 2 = Allow only low resolution printing
; Either the owner or user password must be set for this setting to be honored.
CmdName /appname="pdf" /command="AllowPrinting" /qualifier="2"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Control change permissions. Default qualifier is "1". Legal values are:
; 0 = Do not allow any changes
; 1 = Allow unrestricted changes
; 2 = Allow inserting, deleting, rotating pages
; 3 = Allow filling in form fields and signing
; 4 = Allow commenting, filling in form fields, and signing
; 5 = Allow any changes except for extracting content or printing
; Either the owner or user password must be set for this setting to be honored.
CmdName /appname="pdf" /command="AllowChanges" /qualifier="1"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Specify the RGB raster compression mode.  Zipped by default.
;CmdName /appname="pdf" /command="RGBRasterCompression" /qualifier="jpeg"
CmdName /appname="pdf" /command="RGBRasterCompression" /qualifier="zipped"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Enable/disable searchable text.  On by default.
CmdName /appname="pdf" /command="SearchableText" /qualifier="on"
;CmdName /appname="pdf" /command="SearchableText" /qualifier="off"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Enable or disable 'plot to 3D' functionality.  On by default.
CmdName /appname="pdf" /command="EnablePlotTo3D" /qualifier="on"
;CmdName /appname="pdf" /command="EnablePlotTo3D" /qualifier="off"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Use plot extents for the PDF page size instead of the paper size.
; Off by default.
CmdName /appname="pdf" /command="SetPageFromPlotSize" /qualifier="on"
;CmdName /appname="pdf" /command="SetPageFromPlotSize" /qualifier="off"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Specify the document title string embedded in the PDF file.
; CmdName /appname="pdf" /command="DocTitle" /qualifier="(MS_PLTMODELNAME)"
;------------------------------------------------------------------------------

;------------------------------------------------------------------------------
; Specify the Author string embedded in the PDF file.
; CmdName /appname="pdf" /command="Author" /qualifier="$(USERNAME)"
;------------------------------------------------------------------------------
