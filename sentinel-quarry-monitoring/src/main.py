# main.py
import os
import sys
import time
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# Добавление src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import *
from downloader import SentinelDownloader
from preprocessor import ImagePreprocessor
from indices import IndexCalculator
from detector import QuarryDetector
from vectorizer import Vectorizer
from analyzer import ChangeAnalyzer
from visualizer import Visualizer

def print_banner():
    """Красивый баннер"""
    print("=" * 70)
    print("🚀 МОНИТОРИНГ ПЕСЧАНЫХ КАРЬЕРОВ ПО ДАННЫМ SENTINEL-2")
    print("=" * 70)
    print(f"📍 Область: {AOI_NAME}")
    print(f"📅 Годы анализа: {YEARS[0]} → {YEARS[-1]}")
    print(f"🗺️ Координаты: {AOI_BBOX}")
    print("=" * 70)

def quick_validation(data, year):
    """Быстрая проверка данных"""
    print(f"\n🔍 БЫСТРАЯ ПРОВЕРКА ДАННЫХ {year}:")
    
    if data is None:
        print("❌ Данные не загружены")
        return False
    
    print(f"  Размер массива: {data.shape}")
    print(f"  Каналы: B2, B3, B4, B8, B11, SCL")
    
    # Проверяем SCL канал на облачность
    scl = data[5]
    valid_pixels = np.sum((scl == 4) | (scl == 5) | (scl == 2) | (scl == 3))
    total_pixels = scl.size
    cloud_coverage = 100 * (1 - valid_pixels / total_pixels)
    
    print(f"  Облачность: {cloud_coverage:.1f}%")
    
    if cloud_coverage > 50:
        print("⚠️  Высокая облачность! Могут быть проблемы с анализом")
    
    return True

def test_sand_detection(data, year):
    """Тест детектирования песка"""
    print(f"\n🧪 ТЕСТ ДЕТЕКТИРОВАНИЯ ПЕСКА {year}:")
    
    # Извлекаем каналы
    red = data[2]  # B04
    nir = data[3]  # B08
    swir = data[4] # B11
    
    # Расчёт индексов
    ndvi = (nir - red) / (nir + red + 1e-10)
    ndesi = (swir - nir) / (swir + nir + 1e-10)
    
    # Статистика
    print(f"  NDVI: {np.nanmin(ndvi):.2f} ... {np.nanmax(ndvi):.2f}")
    print(f"  NDESI: {np.nanmin(ndesi):.2f} ... {np.nanmax(ndesi):.2f}")
    
    # Тестовая маска
    sand_mask = (
        (ndvi < THRESHOLDS["NDVI_MAX"]) & 
        (ndesi > THRESHOLDS["NDESI_MIN"]) & 
        (~np.isnan(ndvi))
    )
    
    sand_pixels = np.sum(sand_mask)
    valid_pixels = np.sum(~np.isnan(ndvi))
    
    if valid_pixels > 0:
        sand_percentage = 100 * sand_pixels / valid_pixels
        print(f"  Песчаных пикселей: {sand_pixels} ({sand_percentage:.1f}%)")
        
        if sand_pixels > 100:
            print(f"  ✅ ОБНАРУЖЕНЫ ПЕСЧАНЫЕ ПОВЕРХНОСТИ!")
            return True
        else:
            print(f"  ⚠️  Мало песчаных пикселей")
            return False
    else:
        print("  ❌ Нет валидных пикселей для анализа")
        return False

def create_preview_images(data_2020, data_2025):
    """Создание preview изображений для проверки"""
    print("\n📸 СОЗДАНИЕ ПРЕВЬЮ ИЗОБРАЖЕНИЙ...")
    
    def create_rgb(data, year):
        """Создание RGB изображения"""
        rgb = np.stack([
            np.clip(data[2] * 2.5, 0, 1),  # Red
            np.clip(data[1] * 2.5, 0, 1),  # Green
            np.clip(data[0] * 2.5, 0, 1)   # Blue
        ], axis=-1)
        
        # Сохранение
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(rgb)
        ax.set_title(f"RGB - {AOI_NAME} - {year}")
        ax.axis('off')
        
        filename = os.path.join(OUTPUTS_DIR, f"preview_rgb_{year}.png")
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  RGB {year}: {filename}")
        return filename
    
    def create_sand_composite(data, year):
        """Композит для выделения песка (SWIR-NIR-Red)"""
        composite = np.stack([
            np.clip(data[4] * 3, 0, 1),  # SWIR
            np.clip(data[3] * 3, 0, 1),  # NIR
            np.clip(data[2] * 3, 0, 1)   # Red
        ], axis=-1)
        
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(composite)
        ax.set_title(f"Песок (розовый) - {AOI_NAME} - {year}")
        ax.axis('off')
        
        filename = os.path.join(OUTPUTS_DIR, f"preview_sand_{year}.png")
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  Песочный композит {year}: {filename}")
        return filename
    
    # Создаем изображения
    if data_2020 is not None:
        create_rgb(data_2020, 2020)
        create_sand_composite(data_2020, 2020)
    
    if data_2025 is not None:
        create_rgb(data_2025, 2025)
        create_sand_composite(data_2025, 2025)
    
    print("✅ Превью изображения созданы в папке outputs/")

def main():
    """Основная функция запуска проекта"""
    print_banner()
    
    start_time = time.time()
    overall_success = True
    
    try:
        # ============================================
        # ШАГ 0: ИНИЦИАЛИЗАЦИЯ И ПРОВЕРКА API
        # ============================================
        print("\n[0/8] ПРОВЕРКА API И ПОДКЛЮЧЕНИЯ...")
        downloader = SentinelDownloader()
        print("✅ Sentinel Hub API подключен")
        
        # ============================================
        # ШАГ 1: СКАЧИВАНИЕ ДАННЫХ
        # ============================================
        print(f"\n[1/8] СКАЧИВАНИЕ ДАННЫХ {YEARS}...")
        all_data = {}
        
        for year in YEARS:
            print(f"\n  📥 Скачивание {year}...")
            data = downloader.download_year(year)
            
            if data is not None:
                all_data[year] = data
                quick_validation(data, year)
                test_sand_detection(data, year)
            else:
                print(f"  ❌ Ошибка скачивания {year}")
                overall_success = False
        
        if not all_data:
            print("❌ Нет данных для анализа! Завершение.")
            return
        
        # ============================================
        # ШАГ 2: СОЗДАНИЕ ПРЕВЬЮ
        # ============================================
        print(f"\n[2/8] СОЗДАНИЕ ПРЕВЬЮ ИЗОБРАЖЕНИЙ...")
        if 2020 in all_data and 2025 in all_data:
            create_preview_images(all_data[2020], all_data[2025])
        
        # ============================================
        # ШАГ 3: ПРЕДОБРАБОТКА
        # ============================================
        print(f"\n[3/8] ПРЕДОБРАБОТКА ДАННЫХ...")
        for year in YEARS:
            if year in all_data:
                print(f"  🛠️  Обработка {year}...")
                try:
                    ImagePreprocessor.preprocess_year(year)
                    print(f"  ✅ {year} обработан")
                except Exception as e:
                    print(f"  ❌ Ошибка обработки {year}: {e}")
                    overall_success = False
        
        # ============================================
        # ШАГ 4: РАСЧЁТ ИНДЕКСОВ
        # ============================================
        print(f"\n[4/8] РАСЧЁТ СПЕКТРАЛЬНЫХ ИНДЕКСОВ...")
        for year in YEARS:
            print(f"  📊 Индексы для {year}...")
            try:
                IndexCalculator.calculate_all_indices(year)
                print(f"  ✅ Индексы {year} рассчитаны")
            except Exception as e:
                print(f"  ❌ Ошибка расчёта индексов {year}: {e}")
                overall_success = False
        
        # ============================================
        # ШАГ 5: ДЕТЕКТИРОВАНИЕ КАРЬЕРОВ
        # ============================================
        print(f"\n[5/8] ДЕТЕКТИРОВАНИЕ КАРЬЕРОВ...")
        masks = {}
        for year in YEARS:
            print(f"  🔍 Поиск карьеров {year}...")
            try:
                mask, transform, crs = QuarryDetector.detect_quarries(year)
                masks[year] = mask
                
                if mask is not None:
                    sand_pixels = np.sum(mask)
                    print(f"  ✅ Найдено песчаных пикселей: {sand_pixels}")
                else:
                    print(f"  ⚠️  Карьеры не обнаружены в {year}")
            except Exception as e:
                print(f"  ❌ Ошибка детектирования {year}: {e}")
                overall_success = False
        
        # ============================================
        # ШАГ 6: ВЕКТОРИЗАЦИЯ
        # ============================================
        print(f"\n[6/8] ВЕКТОРИЗАЦИЯ КАРЬЕРОВ...")
        vector_data = {}
        for year in YEARS:
            print(f"  🏞️  Векторизация {year}...")
            try:
                gdf = Vectorizer.vectorize_year(year)
                if gdf is not None:
                    vector_data[year] = gdf
                    area_ha = gdf['area_ha'].sum()
                    print(f"  ✅ {len(gdf)} карьеров, площадь: {area_ha:.2f} га")
                else:
                    print(f"  ⚠️  Нет данных для векторизации {year}")
            except Exception as e:
                print(f"  ❌ Ошибка векторизации {year}: {e}")
                overall_success = False
        
        # ============================================
        # ШАГ 7: АНАЛИЗ ИЗМЕНЕНИЙ
        # ============================================
        print(f"\n[7/8] АНАЛИЗ ИЗМЕНЕНИЙ...")
        changes = None
        if len(YEARS) >= 2 and YEARS[0] in vector_data and YEARS[-1] in vector_data:
            try:
                changes = ChangeAnalyzer.analyze_changes(YEARS[0], YEARS[-1])
                if changes is not None:
                    print(f"  ✅ Анализ изменений завершен")
                else:
                    print(f"  ⚠️  Нет данных об изменениях")
            except Exception as e:
                print(f"  ❌ Ошибка анализа изменений: {e}")
                overall_success = False
        else:
            print(f"  ⚠️  Недостаточно данных для анализа изменений")
        
        # ============================================
        # ШАГ 8: ВИЗУАЛИЗАЦИЯ
        # ============================================
        print(f"\n[8/8] ВИЗУАЛИЗАЦИЯ РЕЗУЛЬТАТОВ...")
        if len(YEARS) >= 2 and changes is not None:
            try:
                visualizer = Visualizer()
                visualizer.create_interactive_map(YEARS[0], YEARS[-1])
                visualizer.create_statistics_plot(changes)
                print(f"  ✅ Визуализация создана")
            except Exception as e:
                print(f"  ❌ Ошибка визуализации: {e}")
                overall_success = False
        
        # ============================================
        # ИТОГИ
        # ============================================
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print("📊 ИТОГИ АНАЛИЗА")
        print("=" * 70)
        
        if overall_success:
            print("✅ ПРОЕКТ УСПЕШНО ЗАВЕРШЕН!")
        else:
            print("⚠️  ПРОЕКТ ЗАВЕРШЕН С ПРЕДУПРЕЖДЕНИЯМИ")
        
        print(f"\n⏱️  Общее время выполнения: {duration:.1f} секунд")
        print(f"📍 Область анализа: {AOI_NAME}")
        
        # Статистика по годам
        for year in YEARS:
            if year in vector_data:
                gdf = vector_data[year]
                print(f"📅 {year}: {len(gdf)} карьеров, {gdf['area_ha'].sum():.2f} га")
        
        if changes is not None:
            print(f"\n📈 ИЗМЕНЕНИЯ {YEARS[0]} → {YEARS[-1]}:")
            for change_type in ["new", "increased", "decreased", "disappeared"]:
                subset = changes[changes["change_type"] == change_type]
                if len(subset) > 0:
                    print(f"  {change_type}: {len(subset)} объектов")
        
        print("\n📁 СОЗДАННЫЕ ФАЙЛЫ:")
        print(f"  📂 Данные: {DATA_DIR}/")
        print(f"  🗺️  Векторные слои: {VECTOR_DIR}/")
        print(f"  📊 Результаты: {OUTPUTS_DIR}/")
        print(f"  🖼️  Превью: {OUTPUTS_DIR}/preview_*.png")
        
        if len(YEARS) >= 2:
            map_file = os.path.join(OUTPUTS_DIR, f"interactive_map_{YEARS[0]}_{YEARS[-1]}.html")
            if os.path.exists(map_file):
                print(f"  🌍 Интерактивная карта: {map_file}")
                print(f"     Открой в браузере для просмотра!")
        
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Процесс прерван пользователем")
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()