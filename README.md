# spoolman-labels

This simple script allows creating and printing of labels for Spoolman Spools

## Features

- Easy to adapt to your needs
- Generates QR Code + Simple identification of the spool (ID, Manufacturer, Filament Name)
- Horizontal or vertical (cropped) images to fit different widths of continuous label rolls
- Prints directly to Brother label printers via `brother_ql` (inventree fork)

## Usage

```shell
usage: spoolman-labels [-h] [-p] [-v] [--printer-model PRINTER_MODEL] [--printer-address PRINTER_ADDRESS]
                       [--label-name LABEL_NAME] [-c] -w WIDTH [-f FONT]
                       SPOOL_ID [SPOOL_ID ...]
```

Define spoolman's address via `-a`/`--spoolman-address`

You must define the label width via `-w`, if you want to print, set `-p` and check the output of `brother_ql info labels` to get the correct name and pixel width for your label, set the label name via `--label-name`
By default the script is configured to print via a USB connected Brother QL-800, you can provide `--printer-model` and `--printer-address`, check `brother_ql info models` to find compatible model strings, and you can try to autodiscover connected printers via `brother_ql discover`

The font option can be the path to a font file, but the `pillow` library will otherwise try to autodiscover the filename in various OS directories (Example: `-f "A-OTF Shin Go Pro B.otf"`)

Using `-c`/`--continuous` will orient the label vertically, and trim empty space to keep the label short.

By default the script saves the label as a png image to the current directory, use `-v` to instead show a preview.

### Examples

Print a horizontal label for spool ID# 41 on a 62mm continuous tape, using Shin Go Pro font

```shell
spoolman-labels -a "https://spoolman.nemexis.org" -w 696 --label-name "62" -p -f "A-OTF Shin Go Pro B.otf" 41
```
