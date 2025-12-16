# preprocessor.py
import numpy as np
import rasterio
from rasterio.transform import from_origin
from config import *

class ImagePreprocessor:
    """Класс для предобработки спутниковых данных"""
    
    @staticmethod
    def apply_cloud_mask(image_data):
        """Маскирование облаков и теней по SCL каналу"""
        # SCL канал (Scene Classification Layer)
        scl = image_data[5]  # 6-й канал в нашем массиве
        
        # Допустимые классы: суша, растительность
        # SCL: 2 - темные пиксели, 3 - облачные тени, 4 - растительность, 
        #      5 - голая почва, 6 - вода, 7-10 - облака
        valid_mask = (scl == 4) | (scl == 5) | (scl == 2) | (scl == 3)
        
        # Применяем маску ко всем каналам
        masked_data = image_data.copy()
        for i in range(5):  # для всех спектральных каналов
            masked_data[i] = np.where(valid_mask, image_data[i], np.nan)
        
        return masked_data
    
    @staticmethod
    def save_as_geotiff(data, year, bbox):
        """Сохранение данных как GeoTIFF"""
        # Порядок каналов: B2, B3, B4, B8, B11, SCL
        channels = ["B02", "B03", "B04", "B08", "B11", "SCL"]
        
        # Трансформация (координаты)
        min_lon, min_lat, max_lon, max_lat = bbox
        pixel_size = RESOLUTION / 111320  # градусов на пиксель (примерно)
        
        transform = from_origin(
            min_lon, 
            max_lat, 
            pixel_size, 
            pixel_size
        )
        
        # Сохранение каждого канала отдельно
        for i, channel in enumerate(channels[:5]):  # только спектральные каналы
            output_path = os.path.join(PROCESSED_DIR, f"{channel}_{year}.tif")
            
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=data.shape[1],
                width=data.shape[2],
                count=1,
                dtype=data.dtype,
                crs='EPSG:4326',
                transform=transform,
            ) as dst:
                dst.write(data[i], 1)
            
            print(f"Сохранен канал {channel} за {year}: {output_path}")
    
    @staticmethod
    def preprocess_year(year):
        """Полный цикл предобработки для одного года"""
        # Загрузка данных
        data_path = os.path.join(RAW_DIR, f"sentinel2_{year}.npy")
        if not os.path.exists(data_path):
            print(f"Данные за {year} не найдены!")
            return None
        
        image_data = np.load(data_path)
        print(f"Загружены данные за {year}. Размер: {image_data.shape}")
        
        # Маскирование облаков
        masked_data = ImagePreprocessor.apply_cloud_mask(image_data)
        
        # Сохранение
        ImagePreprocessor.save_as_geotiff(masked_data, year, AOI_BBOX)
        
        return masked_data


if __name__ == "__main__":
    preprocessor = ImagePreprocessor()
    data_2020 = preprocessor.preprocess_year(2020)