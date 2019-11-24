# kodi-addon-sane-scanner
**A scan tool for Kodi**

This KODI addon enables you to scan documents directly in Kodi, e.g. by using your USB flatbed scanner.

Of course, Kodi isn't this kind of software where you expect to scan documents.
But for me it is convenient to scan and archive my daily mail from my sofa
simply by using my remote control and without opening any desktop application. 

Before I have written this addon I used the scanner buttons with same functionality by
utilizing [scanbd](https://wiki.ubuntuusers.de/scanbd/). But this doesn't work
all the time for some reasons and polls the USB interface all the time in
order to determine if there was an button event. See also problems that I have reported [here](https://bugs.launchpad.net/ubuntu/+source/scanbd/+bug/1747115)

That's why I have written this addon which comes with the following features:
* Kodi-sane-scanner is a *picture addon* 
* configurable devices, dimension, resolution, color mode, brightness, contrast
* scan single or multiple pages
* preview page
* convert to PDF file
* join multiple pages to single document
* add OCR text layer to PDF
* archive PDF in filesystem
* send PDF as email attachment
* print document
* view PDF documents located in archive folder (PDF files in general!)
* rename and delete PDF documents in archive folder via context menu

Here are some screenshots. 

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

Probably you get a message that some priviledges are not available.
In this case you must probably edit ```/etc/ImageMagick-6/policy.xml```
and uncomment the PDF line like this:
```
<!-- <policy domain="coder" rights="none" pattern="PDF" /> -->
```

## OCR

OCR is the hardest. If you want to use OCR you must install ```tesseract-ocr``` and ```ocrmypdf```

I guess that I did the following:

```
apt install \
    python3-pip python-lxml \
    tesseract-ocr tesseract-ocr-deu \
    python-pdfminer python-psycopg2 \
    imagemagick parallel poppler-utils pdftk \
    libtiff-tools qpdf \
    unpaper python-reportlab python-pil ghostscript

pip3 install --upgrade pip  ## Upgrade von pip 8.1.1 auf die aktuelle pip-Version

apt install libffi-dev
pip3 install ocrmypdf
```

Note: ```tesseract-ocr-deu``` is for german language. 

Maybe this is outdated. For latest instructions check these sites:
* [German ubuntusers OCRmyPDF](https://wiki.ubuntuusers.de/OCRmyPDF/)

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