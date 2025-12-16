import os
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from rasterio import features
import rasterio
from config import *

class Vectorizer:
    """Класс для векторизации растровых масок"""

    @staticmethod
    def mask_to_polygons(mask, transform):
        """Преобразование растровой маски в полигоны"""
        shapes_gen = features.shapes(mask.astype(np.uint8), mask=(mask > 0), transform=transform)

        polygons = []
        properties = []
        for geom, value in shapes_gen:
            if value > 0:
                polygon = shape(geom)
                if polygon.area * (RESOLUTION ** 2) >= THRESHOLDS["AREA_MIN"]:
                    polygons.append(polygon)
                    properties.append({
                        "value": int(value),
                        "area_pixels": polygon.area,
                        "area_m2": polygon.area * (RESOLUTION ** 2)
                    })
        return polygons, properties

    @staticmethod
    def create_geodataframe(polygons, properties, crs, year):
        """Создание GeoDataFrame"""
        gdf = gpd.GeoDataFrame(properties, geometry=polygons, crs=crs)
        gdf["year"] = year
        gdf["area_ha"] = gdf["area_m2"] / 10000
        gdf["quarry_id"] = [f"Q_{year}_{i:04d}" for i in range(len(gdf))]
        gdf = gdf.drop(columns=["value", "area_pixels"])
        return gdf

    @staticmethod
    def vectorize_year(year):
        """Векторизация карьеров за год"""
        print(f"Векторизация карьеров за {year} год...")

        mask_path = os.path.join(PROCESSED_DIR, f"quarry_mask_{year}.tif")
        if not os.path.exists(mask_path):
            print(f"Ошибка: маска {mask_path} не найдена!")
            return None

        with rasterio.open(mask_path) as src:
            mask = src.read(1)
            transform = src.transform
            crs = src.crs

        polygons, properties = Vectorizer.mask_to_polygons(mask, transform)
        print(f"  Найдено {len(polygons)} объектов")
        if len(polygons) == 0:
            print(f"  Предупреждение: не найдено объектов для {year} года!")
            return None

        gdf = Vectorizer.create_geodataframe(polygons, properties, crs, year)

        output_path = os.path.join(VECTOR_DIR, f"quarries_{year}.gpkg")
        gdf.to_file(output_path, driver="GPKG")
        print(f"  Векторный слой сохранен: {output_path}")
        print(f"  Общая площадь: {gdf['area_ha'].sum():.2f} га")
        return gdf
