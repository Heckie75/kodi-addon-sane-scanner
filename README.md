# kodi-addon-sane-scanner
**A scan tool for Kodi**

This Kodi add-on allows direct document scanning within Kodi, such as with a USB flatbed scanner.

While Kodi isn't typically used for scanning, this add-on provides a convenient way to scan and archive documents from the couch, using only a remote control.

Before I have written this addon I used the scanner buttons with same functionality by
utilizing [scanbd](https://wiki.ubuntuusers.de/scanbd/). But this doesn't work
all the time for some reasons and polls the USB interface all the time in
order to determine if there was an button event. See also problems that I have reported [here](https://bugs.launchpad.net/ubuntu/+source/scanbd/+bug/1747115)

Here's a cleaned-up version, focusing on clarity and a more professional tone:

This add-on provides the following document scanning features within Kodi:

1. **Picture Add-on:** Integrates seamlessly into Kodi's picture library.
2. **Configurable Scan Settings:** Adjust device, dimensions, resolution, color mode, brightness, and contrast.
3. **Single/Multi-Page Scanning:** Scan individual pages or multiple pages in a single session.
4. **Page Preview:** Review scans before finalizing.
5. **PDF Conversion:** Convert scanned images to PDF format.
6. **Multi-Page PDF Merging:** Combine multiple scanned pages into a single PDF document.
7. **OCR Text Layer:** Add an OCR-generated text layer to PDFs for searchable content.
8. **PDF Archiving:** Save PDFs to a specified file system archive.
9. **Email Attachment:** Send PDFs as email attachments.
10. **Document Printing:** Print scanned documents directly.
11. **PDF Viewing:** View PDF documents stored in the archive folder (or any PDF and many other file types).
12. **Archive Management:** Rename, delete and move  documents within the archive folder via the context menu.

Screenshots are available below.

<img src="plugin.picture.sane-scanner/resources/assets/screenshot_1.png?raw=true">
<sup>Initial screen in Kodi before you have scanned a document</sup>

You can see the already scanned pages and the actions, i.e.
* create PDF
* create PDF and send via email to specific email address
* create PDF and print on specific printer
* remove last page 
* remove all pages

<img src="plugin.picture.sane-scanner/resources/assets/screenshot_2.png?raw=true">
<sup>Screen after you have scanned two pages</sup>

<img src="plugin.picture.sane-scanner/resources/assets/screenshot_3.png?raw=true">
<sup>Preview of scanned page</sup>

Setup dialog for scanner with
* discovery and selection of scanner
* dimension
* mode, i.e. lineart, grayscale or color
* format, i.e. png or jpeg
* resolution
* brightness and contrast

<img src="plugin.picture.sane-scanner/resources/assets/screenshot_settings_1.png?raw=true">
<sup>Setup dialog for scanner</sup>

Output dialog in settings with
* OCR switch
* archive folder for PDF file
* email settings
* printer settings

<img src="plugin.picture.sane-scanner/resources/assets/screenshot_settings_2.png?raw=true">
<sup>Output dialog in settings</sup>
<img src="plugin.picture.sane-scanner/resources/assets/screenshot_settings_3.png?raw=true">
<sup>Output dialog in settings</sup>

## Setup

Before you can use this addon you must setup all the external tools that
this addon utilize, i.e.:
* sane with ```scanimage``` 
* setup a printer
* setup tooling for creating PDF files
* setup tooling for OCR
* setup local email services

Note: Since I am a Ubuntu user I have linked Ubuntu documentation. 

## Scanimage 

The addon utilizes the ```scanimage``` command which provided by sane

Open a terminal and call the following command:
```
$ scanimage -L
device `net:localhost:plustek:libusb:002:015' is a Canon CanoScan LiDE25 flatbed scanner
```

If ```scanimage``` command can't be found or there is no scanner device listed
visit these pages in order to setup your scanner
* [English Ubuntu documentation for SANE](https://help.ubuntu.com/community/sane)
* [German Ubuntusers for SANE](https://wiki.ubuntuusers.de/SANE/)

## Printer

Setting up a printer should be the easiest part. Open a terminal and
check if the folloing command lists printers as expected: 
```
$ lpstat -e
HL-2030-series
```

If there are no printers visit one of the following pages
* [English Ubuntu documentation](https://help.ubuntu.com/stable/ubuntu-help/printing.html.en)
* [German ubuntusers](https://wiki.ubuntuusers.de/Drucker/)

## PDF

Creating PDF files is still not that hard. Open a terminal and
check if you are able to convert an image file to a PDF file like this:

```
convert image.png image.pdf
```

If ```convert``` is not installed follow the instructions and install it.

I have installed the following:
```
sudo apt install imagemagick-6.q16
```

Probably you get a message that some priviledges are not available.
In this case you must probably edit ```/etc/ImageMagick-6/policy.xml```
and uncomment the PDF line like this:
```
<!-- <policy domain="coder" rights="none" pattern="PDF" /> -->
```

## OCR

OCR is the hardest. If you want to use OCR you must install ```tesseract-ocr``` and ```ocrmypdf```

I have installed the following:
```
sudo apt install ocrmypdf imagemagick-6.q16 tesseract-ocr tesseract-ocr-deu
```

Note: ```tesseract-ocr-deu``` is for german language. 

Maybe this is outdated. For latest instructions check these sites:
* [German ubuntusers OCRmyPDF](https://wiki.ubuntuusers.de/OCRmyPDF/)

Note: Please make sure that the file ```ocrmypdf_wrapper``` in addons-folder is executable!

## Send email

Last but not least you maybe want to send you files via email.

Please check if you are able to send an email via command line like this:
```
mail -s "test email" youremail@email.com
```

If this is not the case you must setup _postfix_ (or simular tool)
```
apt install mailutils postfix
```

Of course, you must also configure postfix to your needs. Check instructions here:
* [Ubuntu documentation for Postfix](https://help.ubuntu.com/lts/serverguide/postfix.html)
* [German Ubuntuusers](https://wiki.ubuntuusers.de/Postfix/)

## LibreOffice

To preview some document types in archive it is required that LibreOffice is installed. 

## Limitations, Known Bugs, and End of Maintenance

This Kodi add-on is limited to Linux systems. It is not an official Kodi add-on, as it violates Kodi's policies by executing external programs.

The addon is incompatibility with Flatpak. The following known bugs and limitations exist:

1. **Encoding Issues:** Starting with Ubuntu 24.04, there are problems in context of encoding filenames. There are some fixes starting with version 3.2.0. But it is still not possible to move, print and send files with special characters