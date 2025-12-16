# detector.py
import numpy as np
import cv2
import rasterio
from skimage import measure
import os
from config import *

class QuarryDetector:
    """Детектор песчаных карьеров с учетом затемнений"""

    @staticmethod
    def load_indices(year):
        """Загрузка NDVI, NDESI, NSI и Brightness (яркость)"""
        indices = {}
        transform = None
        crs = None

        for idx_name in ["NDVI", "NDESI", "NSI", "BRIGHTNESS"]:
            file_path = os.path.join(PROCESSED_DIR, f"{idx_name}_{year}.tif")
            with rasterio.open(file_path) as src:
                indices[idx_name] = src.read(1)
                transform = src.transform
                crs = src.crs

        return indices, transform, crs

    @staticmethod
    def detect_sand(indices):
        """Маска песка по спектральным индексам"""
        ndvi = indices["NDVI"]
        ndesi = indices["NDESI"]
        nsi = indices["NSI"]

        sand_mask = (
            (ndvi < THRESHOLDS["NDVI_MAX"]) &
            (ndesi > THRESHOLDS["NDESI_MIN"]) &
            (nsi > THRESHOLDS["NSI_MIN"]) &
            (nsi < THRESHOLDS["NSI_MAX"]) &
            (~np.isnan(ndvi))
        )

        return sand_mask.astype(np.uint8)

    @staticmethod
    def detect_quarries(indices):
        """Выделение карьеров: песок + затемнение"""
        sand_mask = QuarryDetector.detect_sand(indices)
        brightness = indices["BRIGHTNESS"]

        # Маска затемненных участков (например, карьерные выемки)
        dark_mask = (brightness < np.percentile(brightness[sand_mask == 1], 30))
        quarry_mask = sand_mask & dark_mask

        # Морфологическая очистка
        kernel = np.ones((3, 3), np.uint8)
        closed = cv2.morphologyEx(quarry_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=2)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=2)

        # Лейблинг объектов и фильтр по площади
        labeled = measure.label(opened, connectivity=2)
        final_mask = np.zeros_like(labeled, dtype=np.uint8)

        for region in measure.regionprops(labeled):
            if region.area * (RESOLUTION ** 2) >= THRESHOLDS["AREA_MIN"]:
                final_mask[labeled == region.label] = 1

        return final_mask

    @staticmethod
    def save_mask(mask, transform, crs, year):
        """Сохранение маски карьеров"""
        mask_path = os.path.join(PROCESSED_DIR, f"quarry_mask_{year}.tif")
        with rasterio.open(
            mask_path,
            'w',
            driver='GTiff',
            height=mask.shape[0],
            width=mask.shape[1],
            count=1,
            dtype=np.uint8,
            crs=crs,
            transform=transform
        ) as dst:
            dst.write(mask, 1)
        print(f"Маска карьеров сохранена: {mask_path}")
        return mask_path

    @staticmethod
    def detect_year(year):
        print(f"🟣 Детектирование карьеров за {year} год...")
        indices, transform, crs = QuarryDetector.load_indices(year)
        mask = QuarryDetector.detect_quarries(indices)
        mask_path = QuarryDetector.save_mask(mask, transform, crs, year)
        return mask, mask_path


if __name__ == "__main__":
    QuarryDetector.detect_year(2020)
    QuarryDetector.detect_year(2025)
