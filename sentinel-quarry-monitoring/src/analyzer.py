import os
import geopandas as gpd
from config import *

class ChangeAnalyzer:
    """Анализ изменений между годами"""

    @staticmethod
    def load_quarries_data(year):
        path = os.path.join(VECTOR_DIR, f"quarries_{year}.gpkg")
        if not os.path.exists(path):
            print(f"Данные за {year} не найдены")
            return None
        return gpd.read_file(path)

    @staticmethod
    def analyze_changes(year1, year2):
        print(f"Анализ изменений {year1} → {year2}...")
        gdf1 = ChangeAnalyzer.load_quarries_data(year1)
        gdf2 = ChangeAnalyzer.load_quarries_data(year2)

        if gdf1 is None or gdf2 is None:
            print("Недостаточно данных для анализа изменений")
            return None

        changes = []

        # Новые или изменившиеся карьеры
        for idx, row2 in gdf2.iterrows():
            intersect = gdf1[gdf1.intersects(row2.geometry)]
            if intersect.empty:
                changes.append({
                    "quarry_id": row2["quarry_id"],
                    "area_ha_old": 0.0,
                    "area_ha_new": row2["area_ha"],
                    "delta_ha": row2["area_ha"],
                    "change_type": "new",
                    "geometry": row2.geometry
                })
            else:
                area_old = intersect["area_ha"].sum()
                change_type = "increased" if row2["area_ha"] > area_old else "decreased"
                changes.append({
                    "quarry_id": row2["quarry_id"],
                    "area_ha_old": area_old,
                    "area_ha_new": row2["area_ha"],
                    "delta_ha": row2["area_ha"] - area_old,
                    "change_type": change_type,
                    "geometry": row2.geometry
                })

        # Закрытые карьеры
        for idx, row1 in gdf1.iterrows():
            intersect = gdf2[gdf2.intersects(row1.geometry)]
            if intersect.empty:
                changes.append({
                    "quarry_id": f"CLOSED_{row1['quarry_id']}",
                    "area_ha_old": row1["area_ha"],
                    "area_ha_new": 0.0,
                    "delta_ha": -row1["area_ha"],
                    "change_type": "disappeared",
                    "geometry": row1.geometry
                })

        changes_gdf = gpd.GeoDataFrame(changes, geometry="geometry", crs=gdf2.crs)
        output_path = os.path.join(OUTPUTS_DIR, f"changes_{year1}_{year2}.gpkg")
        changes_gdf.to_file(output_path, driver="GPKG")
        print(f"Слой изменений сохранен: {output_path}")

        return changes_gdf
