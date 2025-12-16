# indices.py
import numpy as np
import rasterio
from config import *

class IndexCalculator:
    """Класс для расчёта спектральных индексов"""
    
    @staticmethod
    def load_band(year, band_name):
        """Загрузка одного канала за год"""
        band_map = {
            "RED": "B04",
            "NIR": "B08", 
            "SWIR": "B11",
            "GREEN": "B03",
            "BLUE": "B02"
        }
        
        file_name = f"{band_map[band_name]}_{year}.tif"
        file_path = os.path.join(PROCESSED_DIR, file_name)
        
        with rasterio.open(file_path) as src:
            band = src.read(1)
            transform = src.transform
            crs = src.crs
        
        return band, transform, crs
    
    @staticmethod
    def calculate_ndvi(red, nir):
        """NDVI = (NIR - RED) / (NIR + RED)"""
        with np.errstate(divide='ignore', invalid='ignore'):
            ndvi = (nir - red) / (nir + red)
            ndvi = np.nan_to_num(ndvi, nan=-1, posinf=1, neginf=-1)
        return ndvi
    
    @staticmethod
    def calculate_ndesi(swir, nir):
        """NDESI = (SWIR - NIR) / (SWIR + NIR)"""
        with np.errstate(divide='ignore', invalid='ignore'):
            ndesi = (swir - nir) / (swir + nir)
            ndesi = np.nan_to_num(ndesi, nan=-1, posinf=1, neginf=-1)
        return ndesi
    
    @staticmethod
    def calculate_nsi(red, swir):
        """NSI = (RED - SWIR) / (RED + SWIR)"""
        with np.errstate(divide='ignore', invalid='ignore'):
            nsi = (red - swir) / (red + swir)
            nsi = np.nan_to_num(nsi, nan=-1, posinf=1, neginf=-1)
        return nsi
    
    @staticmethod
    def calculate_all_indices(year):
        """Расчёт всех индексов для указанного года"""
        print(f"Расчёт индексов за {year} год...")
        
        # Загрузка каналов
        red, transform, crs = IndexCalculator.load_band(year, "RED")
        nir, _, _ = IndexCalculator.load_band(year, "NIR")
        swir, _, _ = IndexCalculator.load_band(year, "SWIR")
        
        # Расчёт индексов
        ndvi = IndexCalculator.calculate_ndvi(red, nir)
        ndesi = IndexCalculator.calculate_ndesi(swir, nir)
        nsi = IndexCalculator.calculate_nsi(red, swir)
        
        # Сохранение индексов
        indices = {
            "NDVI": ndvi,
            "NDESI": ndesi, 
            "NSI": nsi
        }
        
        for idx_name, idx_data in indices.items():
            output_path = os.path.join(PROCESSED_DIR, f"{idx_name}_{year}.tif")
            
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=idx_data.shape[0],
                width=idx_data.shape[1],
                count=1,
                dtype=np.float32,
                crs=crs,
                transform=transform,
            ) as dst:
                dst.write(idx_data.astype(np.float32), 1)
            
            print(f"  Сохранен индекс {idx_name}: {output_path}")
        
        return indices, transform, crs


if __name__ == "__main__":
    calculator = IndexCalculator()
    indices_2020 = calculator.calculate_all_indices(2020)