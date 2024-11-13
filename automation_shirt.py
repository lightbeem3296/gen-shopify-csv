import csv
import os
import time
import urllib
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

import requests
from loguru import logger

CUR_DIR = Path(__file__).parent
IMAGE_DIR = CUR_DIR / "images_shirt"
OUTPUT_CSV = CUR_DIR / "output_shirt.csv"
HTTP_TIMEOUT = 15.0
MAX_WORKERS = 32

PRODUCT_TYPES = {
    "tshirt": "T-shirt",
    "longsleeve": "Sweatshirt",
    "longsleeveTshirt": "Long Sleeve T-shirt",
}
PRODUCT_COLORS = {
    "black": "Black",
    "silver": "White",
}
IMAGE_POSITIONS = {
    "1": "CamClose",
    "2": "CamFull",
}
PRODUCT_SIZES = [
    "xs",
    "s",
    "m",
    "l",
    "xl",
    "2xl",
]
IMAGE_HOST_URL = "https://gsimagehost.com/skullz/"


def check_image_exists(image_link: str) -> bool:
    try:
        response = requests.head(image_link, timeout=HTTP_TIMEOUT)
        if response.status_code == 200 and "image" in response.headers["Content-Type"]:
            return True
        else:
            return False
    except requests.Timeout:
        logger.error(f"Request to {image_link} timed out after {HTTP_TIMEOUT} seconds.")
        return False
    except requests.RequestException as e:
        logger.error(f"{e}")
        return False


def extract_product_info(image_filename: str) -> Dict[str, str]:
    words = image_filename.split("_")
    return {
        "handle": words[0].lower().strip(),
        "title": words[0].strip(),
        "type": words[1].strip(),
        "color": words[2].lower().strip(),
    }


def list_images(image_dir: str) -> List[Dict[str, str]]:
    image_list = []
    for filename in os.listdir(image_dir):
        file_ext = os.path.splitext(filename)[-1]
        if file_ext not in [".jpg", ".jpeg", ".png"]:
            logger.warning(f"not an image file: {filename}")
            continue

        info = extract_product_info(image_filename=filename)
        handle = info["handle"]

        exists = False
        for item in image_list:
            if item["handle"] == handle:
                exists = True
                break

        if not exists:
            image_list.append(
                {
                    "filename": filename,
                    "handle": handle,
                    "title": info["title"],
                }
            )
    image_list.sort(key=lambda x: x["filename"])

    return image_list


def gen_img_src_link(title: str, color_tag: str, type_tag: str, size: str) -> str:
    mapping = {
        ("black", "tshirt", "xs"): ("tshirt", "Black", "CamClose"),
        ("black", "tshirt", "s"): ("tshirt", "Black", "CamFull"),
        ("black", "tshirt", "m"): ("tshirt", "White", "CamFull"),
        ("black", "tshirt", "l"): ("longsleeve", "Black", "CamFull"),
        ("black", "tshirt", "xl"): ("longsleeve", "White", "CamFull"),
        ("black", "tshirt", "2xl"): ("longsleeveTshirt", "Black", "CamFull"),
        ("black", "longsleeve", "xs"): ("longsleeveTshirt", "White", "CamFull"),
    }

    final_type_tag, final_color_title, pos_name = mapping.get(
        (color_tag, type_tag, size),
        ("", "", ""),
    )

    img_link = ""
    if pos_name:
        image_name = f"{title}_{final_type_tag}_{final_color_title}_{pos_name}.png"
        img_link = (
            f"{IMAGE_HOST_URL}{urllib.parse.quote(image_name)}?v={int(time.time())}"
        )

    return img_link


def get_variant_image_link(
    title: str,
    color_title: str,
    type_tag: str,
    pos_name: str,
) -> str:
    image_name = f"{title}_{type_tag}_{color_title}_{pos_name}.png"
    return f"{IMAGE_HOST_URL}{urllib.parse.quote(image_name)}?v={int(time.time())}"


def create_inventory_csv(image_dir: str, output_csv: str) -> None:
    img_list = list_images(image_dir=image_dir)

    csv_rows: List[Dict[str, str]] = []
    img_link_list = []
    prev_handle = ""
    for img_info in img_list:
        handle = img_info["handle"]
        title = img_info["title"]
        for color_tag, color_title in PRODUCT_COLORS.items():
            for type_tag, type_title in PRODUCT_TYPES.items():
                for size in PRODUCT_SIZES:
                    logger.info(f"{title} | {color_tag} | {type_title} | {size}")
                    image_src_link = gen_img_src_link(
                        title,
                        color_tag,
                        type_tag,
                        size,
                    )
                    variant_image_link = get_variant_image_link(
                        title,
                        color_title,
                        type_tag,
                        "CamFull",
                    )
                    img_link_list.append(image_src_link)
                    img_link_list.append(variant_image_link)

                    is_new_handle = handle != prev_handle
                    prev_handle = handle

                    if is_new_handle:
                        csv_rows.append(
                            {
                                "Handle": handle,
                                "Title": title,
                                "Body (HTML)": "<ul><li>Great design on a high-quality, soft Bella-Canvas shirt offers comfort and durability.</li><li>Shirt style and design colors may not match the preview exactly due to monitor differences and manufacturing variations.</li></ul>",
                                "Vendor": "My Store",
                                "Product Category": "Apparel & Accessories > Clothing > Clothing Tops > T-Shirts",
                                "Type": type_title,
                                "Tags": "",
                                "Published": "TRUE",
                                "Option1 Name": "Color",
                                "Option1 Value": color_tag,
                                "Option1 Linked To": "product.metafields.shopify.color-pattern",
                                "Option2 Name": "Type",
                                "Option2 Value": type_title,
                                "Option2 Linked To": "",
                                "Option3 Name": "Size",
                                "Option3 Value": size,
                                "Option3 Linked To": "product.metafields.shopify.size",
                                "Variant SKU": "",
                                "Variant Grams": 0,
                                "Variant Inventory Tracker": "shopify",
                                "Variant Inventory Qty": "50",
                                "Variant Inventory Policy": "deny",
                                "Variant Fulfillment Service": "manual",
                                "Variant Price": "20",
                                "Variant Compare At Price": "",
                                "Variant Requires Shipping": "TRUE",
                                "Variant Taxable": "TRUE",
                                "Variant Barcode": "",
                                "Image Src": image_src_link,
                                "Image Position": "",
                                "Image Alt Text": "",
                                "Gift Card": "FALSE",
                                "SEO Title": "",
                                "SEO Description": "",
                                "Google Shopping / Google Product Category": "",
                                "Google Shopping / Gender": "",
                                "Google Shopping / Age Group": "",
                                "Google Shopping / MPN": "",
                                "Google Shopping / Condition": "",
                                "Google Shopping / Custom Product": "",
                                "Google Shopping / Custom Label 0": "",
                                "Google Shopping / Custom Label 1": "",
                                "Google Shopping / Custom Label 2": "",
                                "Google Shopping / Custom Label 3": "",
                                "Google Shopping / Custom Label 4": "",
                                "Clothing features (product.metafields.shopify.clothing-features)": "",
                                "Color (product.metafields.shopify.color-pattern)": "black; silver",
                                "Size (product.metafields.shopify.size)": "xs; s; m; l; xl; 2xl",
                                "Variant Image": variant_image_link,
                                "Variant Weight Unit": "lb",
                                "Variant Tax Code": "",
                                "Cost per item": "",
                                "Included / United States": "TRUE",
                                "Price / United States": "",
                                "Compare At Price / United States": "",
                                "Included / International": "TRUE",
                                "Price / International": "",
                                "Compare At Price / International": "",
                                "Status": "active",
                            }
                        )
                    else:
                        csv_rows.append(
                            {
                                "Handle": handle,
                                "Option1 Value": color_tag,
                                "Option2 Value": type_title,
                                "Option3 Value": size,
                                "Variant Grams": 0,
                                "Variant Inventory Tracker": "shopify",
                                "Variant Inventory Qty": "50",
                                "Variant Inventory Policy": "deny",
                                "Variant Fulfillment Service": "manual",
                                "Variant Price": "20",
                                "Variant Requires Shipping": "TRUE",
                                "Variant Taxable": "TRUE",
                                "Image Src": image_src_link,
                                "Variant Image": variant_image_link,
                                "Variant Weight Unit": "lb",
                            }
                        )

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_rows[0].keys())
        writer.writeheader()  # Write the header
        writer.writerows(csv_rows)  # Write the data
        logger.info(f"Data saved to {output_csv}")

    logger.info("checking image links ...")

    def process_link(link):
        if link != "":
            if check_image_exists(link):
                logger.info(f"exists: {link}")
            else:
                logger.warning(f"image not found: {link}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(process_link, set(img_link_list))


def main():
    logger.info(f"image_folder: {IMAGE_DIR}")
    logger.info(f"image_host_url: {IMAGE_HOST_URL}")
    create_inventory_csv(IMAGE_DIR, OUTPUT_CSV)


if __name__ == "__main__":
    main()
