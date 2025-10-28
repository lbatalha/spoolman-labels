import argparse
import textwrap

import requests
import qrcode

from PIL import Image, ImageDraw, ImageFont

from brother_ql import BrotherQLRaster, create_label
from brother_ql.backends.helpers import send

qr_template = "web+spoolman:s-" # spoolman QR code URI format
qr_border = 4 # 4 is minimum recommended by QR spec

font_scale_header = 0.10
font_scale_body = 0.035

PRINTER = 'usb://0x04f9:0x209b' # QL-800
LABEL_NAME = '62'



def get_spool_qr(spool_id):
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=1, #1px per square, allow pixel perfect upscaling later
        border=qr_border,
    )
    qr.add_data(qr_template + str(spool_id))
    qr.make(fit=False)
    img = qr.make_image()
    return img.get_image()

def main() -> None:
    parser = argparse.ArgumentParser(description="Create label for requested spools")
    parser.add_argument('-p', '--print', action='store_true', help="Print created labels, else save to file $spool_id.png")
    parser.add_argument('-v', '--verbose', action='store_true', help="Show preview of the label")
    parser.add_argument('--printer-model', default='QL-800', help="Printer model")
    parser.add_argument('--printer-address', default='usb://0x04f9:0x209b', help="Printer Address URI")
    parser.add_argument('--label-name', default='62', help="Type of label to print, see `brother_ql info labels`")
    parser.add_argument('-c', '--continuous', action='store_true', help="Generate vertical and cropped label for thin continuous tapes")
    parser.add_argument('-w', '--width', required=True, type=int, help="Label width in pixels, see `brother_ql info labels`")
    parser.add_argument('-f', '--font', default='Arial', type=str, help="Font to use for text (see pillow ImageFont.truetype docs)")
    parser.add_argument('-a', '--spoolman-address', required=True, help="Spoolman Address URI")
    parser.add_argument("SPOOL_ID", nargs='+', type=int, help="Spool IDs to create labels for")
    args = parser.parse_args()

    if args.print:
        qlr = BrotherQLRaster(args.printer_model)

    if args.continuous:
        label_height = args.width
        label_width = label_height*3
        qr_size = label_height
    else:
        label_width = args.width
        qr_size = int(label_width/3)

    for spool in args.SPOOL_ID:
        response = requests.get(f"{args.spoolman_address}/api/v1/spool/{spool}")
        response.raise_for_status()
        data = response.json()

        filament_vendor = data['filament']['vendor']['name']
        filament_name = data['filament']['name']

        print(f"[Spool Info]\nID: {spool}\nManufacturer: {filament_vendor}\nFilament Name: {filament_name}\n")

        qr_img = get_spool_qr(spool)
        qr_scale_factor = qr_size / qr_img.width
        qr_border_size = qr_scale_factor * qr_border
        label_height = qr_size

        # Alpha channel makes it easy to get the proper bounding box later
        image = Image.new("LA", (label_width, label_height), (0,0))

        print(f"Initial Label size: {image.size} px")

        # Draw QR Code
        image.paste(qr_img.resize((qr_size, qr_size)))

        font_size_header = int(label_width*font_scale_header)
        font_size_body = int(label_width*font_scale_body)
        font_header = ImageFont.truetype(args.font, size=font_size_header)
        font_body = ImageFont.truetype(args.font, size=font_size_body)
        body_line_chars = int(label_width / font_size_body / 1.5) #max chars wanted per line for the body, limits line length

        draw = ImageDraw.Draw(image)
        draw.fontmode="L"

        # Draw Header
        draw.text((qr_size, qr_border_size), f"{spool}", font=font_header, fill=(0,255))

        # Draw Body
        text_body = textwrap.wrap(f"{filament_vendor} {filament_name}", \
                                  width=body_line_chars, \
                                  max_lines=3)
        draw.text((qr_size, qr_border_size + font_size_header + font_size_body), \
                  "\n".join(text_body), font=font_body, fill=(0,255))

        bbox = image.getbbox()

        # swap transparency with white background
        label = Image.new("L", (label_width, label_height), (255))
        label.paste(image, mask=image)

        if args.continuous:
            label = label.crop((0, 0, bbox[2]+qr_border_size, bbox[3]))
            label = label.rotate(90, expand=1)

        print(f"Final Label size: {label.size} px")

        if args.verbose:
            label.show()
        if args.print:
            create_label(qlr, label, args.label_name, cut=True, dpi_600=False)
            send(qlr.data, args.printer_address)
        else:
            label.save(f"{spool}.png")
