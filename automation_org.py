import csv
import os
import tkinter as tk
import urllib.parse
from pathlib import Path
from tkinter import messagebox

import requests

# Fixed parameters for each product
# Host url to upload the product images
IMAGE_HOST_URL = "https://gsimagehost.com/skullz/"


CUR_DIR = Path(__file__).parent
# Directory containing the product images
IMAGE_DIR = CUR_DIR / "shirts_4"

# Output CSV file path
OUTPUT_CSV = CUR_DIR / "new_product_inventory_full.csv"

# Description file path
BODY_FILE_PATH = CUR_DIR / "body.txt"


FIXED_VENDOR = "My Store"
FIXED_CATEGORY = "Apparel & Accessories > Clothing > Clothing Tops > T-Shirts"
FIXED_PUBLISHED = "True"
FIXED_FULFILLMENT_SERVICE = "manual"
FIXED_INVENTORY_TRACKER = "shopify"
FIXED_INVENTORY_QTY = 50
FIXED_INVENTORY_POLICY = "deny"
FIXED_WEIGHT_UNIT = "lb"
FIXED_STATUS = "active"
FIXED_TYPE = "T shirt"

# Known colors
FIXED_COLOR = ["Black", "Silver"]
# Map colors from filenames to display colors
COLOR_MAP = {"Black": "Black", "White": "Silver"}
# Known styles
FIXED_STYLES = ["T-Shirt", "Sweatshirt", "Long Sleeve T-Shirt"]
# Map styles from filenames to display styles
STYLES_MAP = {
    "tshirt": "T-Shirt",
    "longsleeve": "Sweatshirt",
    "tshirtlong": "Long Sleeve T-Shirt",
    #'hoodie':'Sweatshirt'
}
# Map price
FIXED_PRICE_MAP = {
    "T-Shirt": "20",
    "Long Sleeve T-Shirt": "20",
    "Sweatshirt": "20",
    #'hoodie': '20',
}
# known size
FIXED_SIZE = ["xs", "s", "m", "l", "xl", "2xl"]
FIXED_OPTION3_LINKED = "product.metafields.shopify.size"

# Create a dictionary by combining colors and styles
# this list use to make image src
FIXED_IMG_LIST = {}
counter = 1  # To keep track of the unique keys
for style in FIXED_STYLES:
    for color in FIXED_COLOR:
        # Create a key-value pair where the value is 'color-style'
        FIXED_IMG_LIST[str(counter)] = f"{color}:{style}"
        counter += 1

# Get the count of items in the dictionary
IMG_COUNT = len(FIXED_IMG_LIST)


def url_encode(text):
    # URL encode the input string
    return urllib.parse.quote(text)


def check_image_exists(url, timeout=10):
    try:
        # Send a HEAD request with a timeout
        response = requests.head(url, timeout=timeout)

        # Check if the request was successful and content-type is an image
        if response.status_code == 200 and "image" in response.headers["Content-Type"]:
            return True
        else:
            return False
    except requests.Timeout:
        # Handle timeout specifically
        print(f"Error: Request to {url} timed out after {timeout} seconds.")
        return False
    except requests.RequestException as e:
        # Handle other possible exceptions
        print(f"Error: {e}")
        return False


def show_alert(url, image_exists):
    # Initialize tkinter
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Show appropriate message box based on the result
    if image_exists:
        messagebox.showinfo("Image Check", f"Image exists at URL: {url}")
    else:
        messagebox.showwarning("Image Check", f"Image does not exist at URL: {url}")

    # Close tkinter root
    root.quit()


def convert_name(name):
    # Split the string at the hyphen
    parts = name.split("-")

    # Capitalize the first letter of each part
    parts = [part.capitalize() for part in parts]

    # Join the parts with a space
    return " ".join(parts)


# Generate SKU for each variant
def generate_sku(product_name, color, style, size):
    return f"{product_name[:4]}-{color[:2]}-{style[:2]}-{size}"


# Extract product information from the filename
def extract_product_info(filename):
    base_name = os.path.splitext(filename)[0]  # Remove file extension
    parts = base_name.split(
        "_"
    )  # Expect structure like 'productname_color_style_imageType_size'

    if len(parts) >= 4:
        product_name = parts[0]
        style = parts[1]
        color = parts[2]
        image_type = parts[3]

        # Map color (e.g., 'white' -> 'silver')
        if color in COLOR_MAP:
            color = COLOR_MAP[color]
        if style in STYLES_MAP:
            style = STYLES_MAP[style]

        return product_name, color, style, image_type
    else:
        return None, None, None, None, None


# Function to find image_src based on style, color, and image_type
def find_image_src(product_images, style, color, image_type):
    for image in product_images:
        if (
            image["style"] == style
            and image["color"] == color
            and image["image_type"] == image_type
        ):
            return image["image_src"]
    return None  # If no match is found


# Create the CSV file with full Shopify product structure and image numbering
def create_inventory_csv(image_dir, output_csv):
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = [
            "Handle",
            "Title",
            "Body (HTML)",
            "Vendor",
            "Product Category",
            "Type",
            "Tags",
            "Published",
            "Option1 Name",
            "Option1 Value",
            "Option1 Linked To",
            "Option2 Name",
            "Option2 Value",
            "Option2 Linked To",
            "Option3 Name",
            "Option3 Value",
            "Option3 Linked To",
            "Variant SKU",
            "Variant Grams",
            "Variant Inventory Tracker",
            "Variant Inventory Qty",
            "Variant Inventory Policy",
            "Variant Fulfillment Service",
            "Variant Price",
            "Variant Compare At Price",
            "Variant Requires Shipping",
            "Variant Taxable",
            "Variant Barcode",
            "Image Src",
            "Image Position",
            "Image Alt Text",
            "Gift Card",
            "SEO Title",
            "SEO Description",
            "Google Shopping / Google Product Category",
            "Google Shopping / Gender",
            "Google Shopping / Age Group",
            "Google Shopping / MPN",
            "Google Shopping / Condition",
            "Color (product.metafields.shopify.color-pattern)",
            "Size (product.metafields.shopify.size)",
            "Variant Image",
            "Variant Weight Unit",
            "Cost per item",
            "Included / United States",
            "Price / United States",
            "Compare At Price / United States",
            "Included / International",
            "Price / International",
            "Compare At Price / International",
            "Status",
        ]

        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        product_images = {}
        for image_filename in os.listdir(image_dir):
            if image_filename.endswith(
                (".jpg", ".jpeg", ".png")
            ):  # Only process image files
                product_name, color, style, image_type = extract_product_info(
                    image_filename
                )

                if product_name and color and style and style in FIXED_STYLES:
                    handle = product_name.lower().replace(" ", "-")
                    title = product_name
                    image_src = IMAGE_HOST_URL + url_encode(image_filename)
                    image_exists = check_image_exists(image_src)
                    # if image_exists == False:
                    # show_alert(image_src, image_exists)
                    # break

                    tags = f"{color}, {style}"

                    # Group images by product for later numbering
                    if handle not in product_images:
                        product_images[handle] = []
                    product_images[handle].append(
                        {
                            "image_src": image_src,
                            "image_type": image_type,
                            "style": style,
                            "color": color,
                        }
                    )

        # Now write the rows with image numbering and variant mapping
        for handle, images in product_images.items():
            image_position = 1

            # Sort images so close-up is first, then other images
            images = sorted(
                images, key=lambda img: img["image_type"] == "CamClose", reverse=True
            )

            product_name = convert_name(handle)
            for color in FIXED_COLOR:
                # Write product details
                for style in FIXED_STYLES:
                    for size in FIXED_SIZE:
                        # firte write product include key information
                        if image_position == 1:
                            with BODY_FILE_PATH.open("r") as body_file:
                                body_txt = body_file.read()

                                writer.writerow(
                                    {
                                        "Handle": handle,
                                        "Title": product_name,
                                        "Body (HTML)": body_txt,
                                        "Vendor": FIXED_VENDOR,
                                        "Product Category": FIXED_CATEGORY,
                                        "Type": "T shirt",
                                        "Published": FIXED_PUBLISHED,
                                        "Option1 Name": "Color",
                                        "Option1 Value": color,
                                        "Option1 Linked To": "product.metafields.shopify.color-pattern",
                                        "Option2 Name": "Type",
                                        "Option2 Value": style,
                                        "Option3 Name": "Size",
                                        "Option3 Value": size,
                                        "Option3 Linked To": "product.metafields.shopify.size",
                                        "Variant Grams": 0,
                                        "Variant Inventory Tracker": FIXED_INVENTORY_TRACKER,
                                        "Variant Inventory Qty": FIXED_INVENTORY_QTY,
                                        "Variant Inventory Policy": FIXED_INVENTORY_POLICY,
                                        "Variant Fulfillment Service": FIXED_FULFILLMENT_SERVICE,
                                        "Variant Price": FIXED_PRICE_MAP[style],
                                        "Variant Requires Shipping": "TRUE",
                                        "Variant Taxable": "TRUE",
                                        "Variant Barcode": "",
                                        "Image Src": find_image_src(
                                            images, style, color, "CamClose"
                                        ),
                                        "Image Position": image_position,
                                        "Gift Card": "FALSE",
                                        "Size (product.metafields.shopify.size)": "xs; s; m; l; xl; 2xl",
                                        "Variant Image": find_image_src(
                                            images, style, color, "CamFull"
                                        ),
                                        "Variant Weight Unit": FIXED_WEIGHT_UNIT,
                                        "Included / United States": "True",
                                        "Included / International": "True",
                                        "Status": FIXED_STATUS,
                                    }
                                )
                        else:
                            # insert all image url to imgsrc at the first section
                            if image_position - 1 <= IMG_COUNT:
                                imgsrc = FIXED_IMG_LIST[str(image_position - 1)]
                                imgsrc_color = imgsrc.strip().split(":", 1)[0]
                                imgsrc_style = imgsrc.strip().split(":", 1)[1]
                                writer.writerow(
                                    {
                                        "Handle": handle,
                                        "Option1 Value": color,
                                        "Option2 Value": style,
                                        "Option3 Value": size,
                                        "Variant Grams": 0,
                                        "Variant Inventory Tracker": FIXED_INVENTORY_TRACKER,
                                        "Variant Inventory Qty": FIXED_INVENTORY_QTY,
                                        "Variant Inventory Policy": FIXED_INVENTORY_POLICY,
                                        "Variant Fulfillment Service": FIXED_FULFILLMENT_SERVICE,
                                        "Variant Price": FIXED_PRICE_MAP[style],
                                        "Variant Requires Shipping": "TRUE",
                                        "Variant Taxable": "TRUE",
                                        "Variant Barcode": "",
                                        "Image Src": find_image_src(
                                            images,
                                            imgsrc_style,
                                            imgsrc_color,
                                            "CamFull",
                                        ),
                                        "Image Position": image_position,
                                        "Variant Image": find_image_src(
                                            images, style, color, "CamFull"
                                        ),
                                        "Variant Weight Unit": FIXED_WEIGHT_UNIT,
                                        "Included / United States": "True",
                                        "Included / International": "True",
                                        "Status": FIXED_STATUS,
                                    }
                                )
                            else:
                                writer.writerow(
                                    {
                                        "Handle": handle,
                                        "Option1 Value": color,
                                        "Option2 Value": style,
                                        "Option3 Value": size,
                                        "Variant Grams": 0,
                                        "Variant Inventory Tracker": FIXED_INVENTORY_TRACKER,
                                        "Variant Inventory Qty": FIXED_INVENTORY_QTY,
                                        "Variant Inventory Policy": FIXED_INVENTORY_POLICY,
                                        "Variant Fulfillment Service": FIXED_FULFILLMENT_SERVICE,
                                        "Variant Price": FIXED_PRICE_MAP[style],
                                        "Variant Requires Shipping": "TRUE",
                                        "Variant Taxable": "TRUE",
                                        "Variant Barcode": "",
                                        "Variant Image": find_image_src(
                                            images, style, color, "CamFull"
                                        ),
                                        "Variant Weight Unit": FIXED_WEIGHT_UNIT,
                                        "Included / United States": "True",
                                        "Included / International": "True",
                                        "Status": FIXED_STATUS,
                                    }
                                )
                        image_position += 1
    print(f"The csv file created! {OUTPUT_CSV}")


# Example usage:
create_inventory_csv(IMAGE_DIR, OUTPUT_CSV)
