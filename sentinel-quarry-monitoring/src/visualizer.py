import os
import folium
import matplotlib.pyplot as plt
import geopandas as gpd
from config import *

class Visualizer:
    """Визуализация карьеров и изменений"""

    @staticmethod
    def create_interactive_map(year1, year2):
        gdf1_path = os.path.join(VECTOR_DIR, f"quarries_{year1}.gpkg")
        gdf2_path = os.path.join(VECTOR_DIR, f"quarries_{year2}.gpkg")
        changes_path = os.path.join(OUTPUTS_DIR, f"changes_{year1}_{year2}.gpkg")

        gdf1 = gpd.read_file(gdf1_path) if os.path.exists(gdf1_path) else gpd.GeoDataFrame()
        gdf2 = gpd.read_file(gdf2_path) if os.path.exists(gdf2_path) else gpd.GeoDataFrame()
        changes = gpd.read_file(changes_path) if os.path.exists(changes_path) else gpd.GeoDataFrame()

        center_lat = (AOI_BBOX[1] + AOI_BBOX[3]) / 2
        center_lon = (AOI_BBOX[0] + AOI_BBOX[2]) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB positron")

        # Карьеры year1
        if not gdf1.empty:
            folium.GeoJson(
                gdf1,
                name=f"Карьеры {year1}",
                style_function=lambda x: {'fillColor': 'red', 'color': 'red', 'weight': 1, 'fillOpacity': 0.5},
                tooltip=folium.GeoJsonTooltip(fields=["quarry_id", "area_ha"], aliases=["ID", "Площадь (га)"])
            ).add_to(m)

        # Карьеры year2
        if not gdf2.empty:
            folium.GeoJson(
                gdf2,
                name=f"Карьеры {year2}",
                style_function=lambda x: {'fillColor': 'red', 'color': 'red', 'weight': 1, 'fillOpacity': 0.5},
                tooltip=folium.GeoJsonTooltip(fields=["quarry_id", "area_ha"], aliases=["ID", "Площадь (га)"])
            ).add_to(m)

        # Изменения
        if not changes.empty:
            def style_change(feature):
                color_map = {
                    "new": "green",
                    "increased": "orange",
                    "decreased": "yellow",
                    "disappeared": "purple"
                }
                t = feature["properties"].get("change_type", "")
                return {'fillColor': color_map.get(t, "gray"), 'color': color_map.get(t, "gray"), 'weight': 2, 'fillOpacity': 0.5}

            folium.GeoJson(
                changes,
                name="Изменения",
                style_function=style_change,
                tooltip=folium.GeoJsonTooltip(fields=["quarry_id", "change_type", "delta_ha"],
                                              aliases=["ID", "Тип изменения", "Δ площадь (га)"])
            ).add_to(m)

        folium.LayerControl().add_to(m)
        map_path = os.path.join(OUTPUTS_DIR, f"interactive_map_{year1}_{year2}.html")
        m.save(map_path)
        print(f"Интерактивная карта сохранена: {map_path}")
        return m

    @staticmethod
    def create_statistics_plot(changes_gdf):
        if changes_gdf.empty:
            print("Нет данных для графиков")
            return
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        change_counts = changes_gdf["change_type"].value_counts()
        axes[0, 0].bar(change_counts.index, change_counts.values, color="skyblue")
        axes[0, 0].set_title("Количество объектов по типам изменений")
        axes[0, 0].set_ylabel("Количество")

        for t in changes_gdf["change_type"].unique():
            subset = changes_gdf[changes_gdf["change_type"] == t]
            axes[0, 1].hist(subset["delta_ha"], bins=20, alpha=0.5, label=t)
        axes[0, 1].set_title("Распределение изменений площади")
        axes[0, 1].set_xlabel("Δ площадь (га)")
        axes[0, 1].legend()

        total_changes = changes_gdf.groupby("change_type")["delta_ha"].sum()
        axes[1, 0].bar(total_changes.index, total_changes.values, color="coral")
        axes[1, 0].set_title("Суммарные изменения площади")
        axes[1, 0].set_ylabel("Площадь (га)")

        axes[1, 1].pie(change_counts.values, labels=change_counts.index, autopct='%1.1f%%', startangle=90)
        axes[1, 1].set_title("Процентное распределение изменений")
        plt.tight_layout()

        plot_path = os.path.join(OUTPUTS_DIR, "statistics_plot.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"График сохранен: {plot_path}")
        plt.show()
