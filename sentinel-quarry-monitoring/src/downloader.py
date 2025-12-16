# src/downloader.py

import os
import numpy as np
import calendar

from sentinelhub import (
    SHConfig,
    BBox,
    CRS,
    DataCollection,
    SentinelHubRequest,
    MimeType,
    bbox_to_dimensions,
    MosaickingOrder
)

from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    AOI_BBOX,
    RESOLUTION,
    SEASON,
    MAX_CLOUD_COVERAGE,
    YEARS,
    RAW_DIR,
)


class SentinelDownloader:
    """Скачивание Sentinel-2 L2A через Sentinel Hub"""

    def __init__(self):
        self.config = SHConfig()
        self.config.sh_client_id = CLIENT_ID
        self.config.sh_client_secret = CLIENT_SECRET
        self.config.save_token = True
        self.config.token_path = os.path.abspath(".sentinel-token")

        self.aoi_bbox = BBox(bbox=AOI_BBOX, crs=CRS.WGS84)
        self.aoi_size = bbox_to_dimensions(self.aoi_bbox, resolution=RESOLUTION)

        print(f"✅ Область интереса: {AOI_BBOX}")
        print(f"✅ CRS: EPSG:4326")
        print(f"✅ Размер изображения (пиксели): {self.aoi_size}")

    def get_evalscript(self):
        """Evalscript v3 — ОДИН input (критично важно)"""
        return """
        //VERSION=3
        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04", "B08", "B11", "SCL"],
                    units: ["REFLECTANCE", "REFLECTANCE", "REFLECTANCE", "REFLECTANCE", "REFLECTANCE", "DN"]
                }],
                output: {
                    bands: 6,
                    sampleType: "FLOAT32"
                }
            };
        }

        function evaluatePixel(sample) {
            return [
                sample.B02,
                sample.B03,
                sample.B04,
                sample.B08,
                sample.B11,
                sample.SCL
            ];
        }
        """

    def download_year(self, year):
        start_month = SEASON["start_month"]
        end_month = SEASON["end_month"]
        _, last_day = calendar.monthrange(year, end_month)

        start_date = f"{year}-{start_month:02d}-01"
        end_date = f"{year}-{end_month:02d}-{last_day:02d}"

        print(f"\n📥 Скачивание данных за {year} ({start_date} – {end_date})...")

        try:
            input_data = SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(start_date, end_date),
                maxcc=MAX_CLOUD_COVERAGE,
                mosaicking_order=MosaickingOrder.LEAST_CC,
            )

            request = SentinelHubRequest(
                evalscript=self.get_evalscript(),
                input_data=[input_data],
                responses=[
                    SentinelHubRequest.output_response("default", MimeType.TIFF)
                ],
                bbox=self.aoi_bbox,
                size=self.aoi_size,
                config=self.config,
            )

            data = request.get_data()
            if not data:
                print("⚠️ Нет данных за период")
                return None

            image = data[0]
            print(f"✅ Получено изображение: {image.shape} (H × W × C)")

            os.makedirs(RAW_DIR, exist_ok=True)
            out_path = os.path.join(RAW_DIR, f"sentinel2_{year}.npy")

            image_chw = np.transpose(image, (2, 0, 1))
            np.save(out_path, image_chw)

            print(f"💾 Сохранено: {out_path}")
            print(f"📐 Формат: {image_chw.shape} (C × H × W)")

            return image_chw

        except Exception as e:
            print(f"❌ Ошибка при скачивании {year}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def download_all_years(self):
        all_data = {}
        for year in YEARS:
            data = self.download_year(year)
            if data is not None:
                all_data[year] = data
        return all_data
