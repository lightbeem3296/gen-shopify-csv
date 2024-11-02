import csv
import os
import random
import time
import urllib
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import requests
from loguru import logger

CUR_DIR = Path(__file__).parent
IMAGE_DIR = CUR_DIR / "images"
OUTPUT_CSV = CUR_DIR / "output.csv"
HTTP_TIMEOUT = 15.0
IMAGE_POSITIONS = {
    "1": "CamGallery",
    "2": "Cam1",
    "3": "Cam2",
    "4": "CamClose",
}

CHECK_IMAGE_LINK = True
IMAGE_HOST_URL = "https://gsimagehost.com/macrocentric/"


def extract_product_info(image_filename: str) -> Dict[str, str]:
    words = image_filename.split("_")
    return {
        "handle": words[0].lower().strip(),
        "title": words[0].strip(),
        "type": words[1].strip(),
    }


def get_random_time_in_date_range(start_year, start_month, end_year, end_month) -> str:
    """Returns random date in range. For example `October 2023`."""
    start_date = datetime(start_year, start_month, 1)
    if end_month == 12:
        end_date = datetime(end_year + 1, 1, 1)
    else:
        end_date = datetime(end_year, end_month + 1, 1)

    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))

    random_time = start_date + timedelta(seconds=random_seconds)
    return random_time.strftime("%B %Y")


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


def create_inventory_csv(image_dir: str, output_csv: str) -> None:
    image_info_list: List[Dict[str, str]] = []
    for image_filename in os.listdir(image_dir):
        file_ext = os.path.splitext(image_filename)[-1]
        if file_ext not in [".jpg", ".jpeg", ".png"]:
            continue

        image_info = extract_product_info(image_filename=image_filename)
        for pos_index, pos_name in IMAGE_POSITIONS.items():
            image_name = f'{image_info["title"]}_{image_info["type"]}_{pos_name}.png'
            logger.info(f"image_name: {image_name}")

            image_src_link = (
                f"{IMAGE_HOST_URL}{urllib.parse.quote(image_name)}?v={time.time()}"
            )

            if CHECK_IMAGE_LINK:
                if check_image_exists(image_src_link):
                    logger.info("exists")
                else:
                    logger.warning(f"image not found: {image_src_link}")

            if pos_index == "1":
                image_info_list.append(
                    {
                        "Handle": image_info["handle"],
                        "Title": image_info["title"],
                        "Body (HTML)": "",
                        "Vendor": "My Store",
                        "Product Category": "Software > Digital Goods & Currency > Digital Artwork",
                        "Type": image_info["type"],
                        "Tags": "",
                        "Published": "TRUE",
                        "Collection": get_random_time_in_date_range(2023, 8, 2024, 11),
                        "Option1 Name": "Title",
                        "Option1 Value": "Default Title",
                        "Option1 Linked To": "",
                        "Option2 Name": "",
                        "Option2 Value": "",
                        "Option2 Linked To": "",
                        "Option3 Name": "",
                        "Option3 Value": "",
                        "Option3 Linked To": "",
                        "Variant SKU": "",
                        "Variant Grams": "0",
                        "Variant Inventory Tracker": "shopify",
                        "Variant Inventory Qty": "0",
                        "Variant Inventory Policy": "continue",
                        "Variant Fulfillment Service": "manual",
                        "Variant Price": "485",
                        "Variant Compare At Price": "",
                        "Variant Requires Shipping": "TRUE",
                        "Variant Taxable": "TRUE",
                        "Variant Barcode": "",
                        "Image Src": image_src_link,
                        "Image Position": pos_index,
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
                        "Variant Image": "",
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
                image_info_list.append(
                    {
                        "Handle": image_info["handle"],
                        "Image Src": image_src_link,
                        "Image Position": pos_index,
                    }
                )

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=image_info_list[0].keys())
        writer.writeheader()  # Write the header
        writer.writerows(image_info_list)  # Write the data

    logger.info(f"Data saved to {output_csv}")


def main():
    create_inventory_csv(IMAGE_DIR, OUTPUT_CSV)


if __name__ == "__main__":
    input("Press ENTER to exit.")
