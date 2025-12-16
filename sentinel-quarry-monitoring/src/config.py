# config.py
import os
from datetime import datetime

# ====================
# API КЛЮЧИ SENTINEL HUB
# ====================
CLIENT_ID = "494c53a6-ef1d-4f41-aafb-0728e50965da"
CLIENT_SECRET = "GVJhXU4bOmmdaw4zAK0CNYw5dLBCjuyQ"

# ====================
# ВЫБЕРИ ОДИН ИЗ ВАРИАНТОВ НИЖЕ!
# ====================

# ВАРИАНТ 1: Крупный карьер в Раменском районе (Московская обл.)
# Самый надежный вариант - большой песчаный карьер
AOI_BBOX = [113.95, 62.48, 114.05, 62.53]  # [min_lon, min_lat, max_lon, max_lat]
AOI_NAME = "Раменский_карьер"

# ВАРИАНТ 2: Несколько карьеров в Чеховском районе
# AOI_BBOX = [37.55, 55.10, 37.75, 55.25]
# AOI_NAME = "Чеховский_карьер"

# ВАРИАНТ 3: Карьер во Всеволожском районе (Ленинградская обл.)
# AOI_BBOX = [30.50, 59.90, 30.70, 60.05]
# AOI_NAME = "Всеволожский_карьер"

# ====================
# ПАРАМЕТРЫ АНАЛИЗА
# ====================

# Временные периоды
YEARS = [2020, 2025]
SEASON = {
    "start_month": 5,    # май (лучшая видимость после схода снега)
    "end_month": 9       # сентябрь (до осенних дождей)
}

# ====================
# ПАРАМЕТРЫ ОБРАБОТКИ
# ====================
RESOLUTION = 10  # метров на пиксель
MAX_CLOUD_COVERAGE = 0.2  # максимальная облачность 20% (строже для теста)

# ====================
# ПОРОГИ ДЛЯ КЛАССИФИКАЦИИ ПЕСКА
# ====================
THRESHOLDS = {
    "NDVI_MAX": 0.25,      # Песок имеет низкий NDVI (растительности почти нет)
    "NDESI_MIN": 0.35,     # Песок имеет высокий NDESI (очень сухая поверхность)
    "NSI_MIN": -0.25,      # Диапазон NSI для песка
    "NSI_MAX": 0.25,
    "AREA_MIN": 1000,      # Минимальная площадь карьера (1000 кв.м = 0.1 га)
}

# ====================
# ПУТИ К ФАЙЛАМ
# ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
VECTOR_DIR = os.path.join(DATA_DIR, "vector")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")

# Создание директорий
for dir_path in [RAW_DIR, PROCESSED_DIR, VECTOR_DIR, OUTPUTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ====================
# ЛОГИРОВАНИЕ
# ====================
LOG_FILE = os.path.join(BASE_DIR, f"quarry_monitoring_{AOI_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")