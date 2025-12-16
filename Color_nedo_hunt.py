"""
Инструмент для перекрашивания цветовых палитр
Стилизованный дизайн в тематике рисования и дизайна
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from PIL import ImageColor
import numpy as np
import re
import colorsys
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# МОДЕЛИ ДАННЫХ
# ============================================================================

class RecolorMode(Enum):
    """Режимы перекраски цветов"""
    KEEP_HUE = "keep_hue"
    FULL_RECOLOR = "full_recolor"
    MIXED = "mixed"


@dataclass
class ColorResult:
    """Результат обработки цвета"""
    original: str
    new_color: str
    luminance: float


# ============================================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С ЦВЕТАМИ
# ============================================================================

class ColorUtility:
    """Утилиты для работы с цветами"""
    
    CYRILLIC_TO_LATIN = {
        'а': 'a', 'в': 'b', 'с': 'c', 'е': 'e', 'к': 'k', 'м': 'm', 'о': 'o',
        'р': 'p', 'т': 't', 'х': 'x', 'у': 'y', 'ё': 'e', 'ъ': '', 'ь': '',
        'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    
    @staticmethod
    def relative_luminance(rgb: Tuple[int, int, int]) -> float:
        """Вычисляет относительную яркость цвета"""
        def adjust(channel: float) -> float:
            return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        
        r, g, b = [x / 255.0 for x in rgb]
        r, g, b = adjust(r), adjust(g), adjust(b)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    @classmethod
    def normalize_color(cls, color: str) -> str:
        """Нормализует строку цвета"""
        if not color:
            return color
        
        color = color.strip().lower()
        
        # Заменяем кириллицу на латиницу
        for cyr, lat in cls.CYRILLIC_TO_LATIN.items():
            color = color.replace(cyr, lat)
        
        # Удаляем недопустимые символы
        color = re.sub(r'[^0-9a-f#]', '', color)
        
        # Обработка различных форматов
        if color.startswith('#'):
            if len(color) == 4:  # #rgb -> #rrggbb
                return '#' + ''.join(c * 2 for c in color[1:])
            return color.lower()
        
        if len(color) == 3:  # rgb -> #rrggbb
            return '#' + ''.join(c * 2 for c in color)
        
        if len(color) == 6:  # rrggbb -> #rrggbb
            return '#' + color
        
        return color
    
    @classmethod
    def is_valid_color(cls, color: str) -> bool:
        """Проверяет валидность цвета"""
        if not color or not color.strip():
            return False
        
        normalized = cls.normalize_color(color)
        if not normalized:
            return False
        
        try:
            ImageColor.getrgb(normalized)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Преобразует RGB в HEX"""
        return "#{:02x}{:02x}{:02x}".format(*rgb)
    
    @staticmethod
    def get_complementary_color(hex_color: str) -> str:
        """Возвращает дополнительный цвет"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        complementary = tuple(255 - c for c in rgb)
        return ColorUtility.rgb_to_hex(complementary)


# ============================================================================
# СТРАТЕГИИ ПЕРЕКРАСКИ
# ============================================================================

class RecolorStrategy(ABC):
    """Базовый класс для стратегий перекраски"""
    
    @abstractmethod
    def recolor(self, original_hls: Tuple[float, float, float],
                target_hls: Tuple[float, float, float],
                luminance_ratio: float,
                intensity: float) -> Tuple[float, float, float]:
        """Выполняет перекраску цвета"""
        pass


class KeepHueStrategy(RecolorStrategy):
    """Стратегия с сохранением исходного оттенка"""
    
    def recolor(self, original_hls: Tuple[float, float, float],
                target_hls: Tuple[float, float, float],
                luminance_ratio: float,
                intensity: float) -> Tuple[float, float, float]:
        orig_h, orig_l, orig_s = original_hls
        target_h, target_l, target_s = target_hls
        
        new_h = orig_h
        new_l = 0.2 + 0.7 * luminance_ratio
        new_s = target_s * 0.7 + orig_s * 0.3
        
        # Применяем интенсивность
        if intensity < 1.0:
            new_h = orig_h * (1 - intensity) + new_h * intensity
            new_s = orig_s * (1 - intensity) + new_s * intensity
            new_l = orig_l * (1 - intensity) + new_l * intensity
        
        return new_h, new_l, new_s


class FullRecolorStrategy(RecolorStrategy):
    """Стратегия полной перекраски"""
    
    def recolor(self, original_hls: Tuple[float, float, float],
                target_hls: Tuple[float, float, float],
                luminance_ratio: float,
                intensity: float) -> Tuple[float, float, float]:
        orig_h, orig_l, orig_s = original_hls
        target_h, target_l, target_s = target_hls
        
        new_h = target_h
        
        # Корректируем яркость в зависимости от палитры
        max_orig_lum = luminance_ratio  # Используем как индикатор
        if max_orig_lum > 0.7:
            new_l = 0.5 + 0.4 * luminance_ratio
        else:
            new_l = 0.2 + 0.5 * luminance_ratio
        
        orig_lum = ColorUtility.relative_luminance(
            tuple(int(c * 255) for c in colorsys.hls_to_rgb(orig_h, orig_l, orig_s))
        )
        new_s = target_s * (0.8 + 0.2 * (1 - orig_lum))
        
        # Применяем интенсивность
        if intensity < 1.0:
            new_h = orig_h * (1 - intensity) + new_h * intensity
            new_s = orig_s * (1 - intensity) + new_s * intensity
            new_l = orig_l * (1 - intensity) + new_l * intensity
        
        return new_h, new_l, new_s


class MixedStrategy(RecolorStrategy):
    """Смешанная стратегия"""
    
    def recolor(self, original_hls: Tuple[float, float, float],
                target_hls: Tuple[float, float, float],
                luminance_ratio: float,
                intensity: float) -> Tuple[float, float, float]:
        orig_h, orig_l, orig_s = original_hls
        target_h, target_l, target_s = target_hls
        
        new_h = orig_h * (1 - intensity) + target_h * intensity
        new_l = orig_l * (1 - intensity) + (0.3 + 0.6 * luminance_ratio) * intensity
        new_s = orig_s * (1 - intensity) + target_s * intensity
        
        return new_h, new_l, new_s


class StrategyFactory:
    """Фабрика для создания стратегий перекраски"""
    
    _strategies = {
        RecolorMode.KEEP_HUE: KeepHueStrategy(),
        RecolorMode.FULL_RECOLOR: FullRecolorStrategy(),
        RecolorMode.MIXED: MixedStrategy()
    }
    
    @classmethod
    def get_strategy(cls, mode: RecolorMode) -> RecolorStrategy:
        """Возвращает стратегию по режиму"""
        return cls._strategies.get(mode, cls._strategies[RecolorMode.FULL_RECOLOR])


# ============================================================================
# ОСНОВНОЙ СЕРВИС ПЕРЕКРАСКИ
# ============================================================================

class ColorRecolorService:
    """Сервис для перекраски палитр цветов"""
    
    def __init__(self):
        self.color_util = ColorUtility()
    
    def recolor_palette(self, original_colors: List[str], 
                       target_base: str, 
                       intensity: float, 
                       mode: RecolorMode) -> List[ColorResult]:
        """Перекрашивает палитру цветов"""
        
        # Валидация и нормализация входных цветов
        valid_colors = [
            self.color_util.normalize_color(c) 
            for c in original_colors 
            if self.color_util.is_valid_color(c)
        ]
        
        if not valid_colors:
            return []
        
        # Получаем целевой цвет
        target_rgb = np.array(ImageColor.getrgb(target_base)) / 255.0
        target_hls = colorsys.rgb_to_hls(*target_rgb)
        
        # Вычисляем яркости исходных цветов
        luminances = [
            self.color_util.relative_luminance(ImageColor.getrgb(c))
            for c in valid_colors
        ]
        
        min_lum, max_lum = min(luminances), max(luminances)
        lum_range = max_lum - min_lum if max_lum != min_lum else 1.0
        
        # Получаем стратегию перекраски
        strategy = StrategyFactory.get_strategy(mode)
        
        results = []
        for color, orig_lum in zip(valid_colors, luminances):
            # Получаем исходный цвет в HLS
            rgb = np.array(ImageColor.getrgb(color)) / 255.0
            orig_hls = colorsys.rgb_to_hls(*rgb)
            
            # Вычисляем относительную яркость
            lum_ratio = (orig_lum - min_lum) / lum_range if lum_range > 0 else 0.5
            
            # Применяем стратегию
            new_h, new_l, new_s = strategy.recolor(orig_hls, target_hls, lum_ratio, intensity)
            
            # Ограничиваем значения
            new_h = np.clip(new_h, 0.0, 1.0)
            new_s = np.clip(new_s, 0.1, 1.0)
            new_l = np.clip(new_l, 0.1, 0.95)
            
            # Конвертируем обратно в RGB
            new_rgb = colorsys.hls_to_rgb(new_h, new_l, new_s)
            new_rgb_int = tuple(int(round(x * 255)) for x in new_rgb)
            
            new_color_hex = self.color_util.rgb_to_hex(new_rgb_int)
            new_luminance = self.color_util.relative_luminance(new_rgb_int)
            
            results.append(ColorResult(color, new_color_hex, new_luminance))
        
        return results


# ============================================================================
# GUI КОМПОНЕНТЫ С ХУДОЖЕСТВЕННЫМ ДИЗАЙНОМ
# ============================================================================

class ContextMenuMixin:
    """Миксин для добавления контекстного меню"""
    
    @staticmethod
    def add_context_menu(widget):
        """Добавляет контекстное меню к виджету"""
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Копировать", command=lambda: widget.event_generate('<<Copy>>'))
        menu.add_command(label="Вставить", command=lambda: widget.event_generate('<<Paste>>'))
        menu.add_command(label="Вырезать", command=lambda: widget.event_generate('<<Cut>>'))
        menu.add_separator()
        menu.add_command(label="Выделить все", 
                        command=lambda: widget.select_range(0, tk.END) if hasattr(widget, 'select_range') 
                        else widget.tag_add(tk.SEL, "1.0", tk.END))
        
        def show_menu(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        
        widget.bind("<Button-3>", show_menu)
        return menu


class StyledFrame(tk.Frame):
    """Стилизованный фрейм с художественным оформлением"""
    
    def __init__(self, parent, **kwargs):
        style_config = {
            'bg': '#2c3e50',
            'bd': 0,
            'highlightthickness': 0,
            'relief': 'flat'
        }
        style_config.update(kwargs)
        super().__init__(parent, **style_config)


class ColorPaletteFrame(StyledFrame):
    """Художественная палитра цветов"""
    
    def __init__(self, parent, title: str, icon: str = "🎨"):
        super().__init__(parent)
        
        # Заголовок с иконкой
        header_frame = StyledFrame(self, bg='#34495e')
        header_frame.pack(fill='x', pady=(0, 5))
        
        title_label = tk.Label(header_frame, text=f"  {icon} {title}", 
                font=('Segoe UI', 11, 'bold'),
                bg='#34495e', fg='#ecf0f1', anchor='w')
        title_label.pack(side='left', fill='x', padx=10, pady=8)
        
        # Основной контент
        self.content_frame = StyledFrame(self, bg='#ffffff')
        self.content_frame.pack(fill='both', expand=True, padx=2, pady=(0, 2))
        
        self.entries: List[tk.Entry] = []
        self.previews: List[tk.Label] = []
    
    def create_color_inputs(self, count: int):
        """Создает поля для ввода цветов"""
        # Очищаем старые виджеты
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.entries.clear()
        self.previews.clear()
        
        # Создаем сетку
        for i in range(count):
            row_frame = StyledFrame(self.content_frame, bg='#ffffff')
            row_frame.pack(fill='x', pady=4, padx=10)
            
            # Номер цвета
            number_label = tk.Label(row_frame, text=f"{i+1}.", font=('Segoe UI', 10),
                                   bg='#ffffff', fg='#7f8c8d', width=3)
            number_label.pack(side='left')
            
            # Превью цвета (больше и с тенью)
            preview_frame = StyledFrame(row_frame, bg='#ffffff')
            preview_frame.pack(side='left', padx=(0, 10))
            
            preview = tk.Label(preview_frame, width=6, height=1, 
                             relief='ridge', borderwidth=2,
                             bg='#ffffff', highlightbackground='#bdc3c7',
                             cursor="hand2")
            preview.pack()
            preview.bind("<Button-1>", lambda e, idx=i: self._choose_color(idx))
            self.previews.append(preview)
            
            # Поле ввода с художественным стилем
            entry_frame = StyledFrame(row_frame, bg='#ffffff')
            entry_frame.pack(side='left', fill='x', expand=True)
            
            entry = tk.Entry(entry_frame, font=('Segoe UI', 10),
                           relief='flat', bd=2, highlightthickness=1,
                           highlightcolor='#3498db', highlightbackground='#bdc3c7',
                           bg='#f8f9fa', fg='#2c3e50')
            entry.pack(fill='x', ipady=3)
            entry.bind('<KeyRelease>', lambda e, idx=i: self._update_preview(idx))
            entry.bind('<FocusIn>', lambda e: entry.configure(highlightbackground='#3498db'))
            entry.bind('<FocusOut>', lambda e: entry.configure(highlightbackground='#bdc3c7'))
            
            ContextMenuMixin.add_context_menu(entry)
            self.entries.append(entry)
            
            # Кнопка выбора цвета (иконка вместо текста)
            btn = tk.Button(row_frame, text="🖌️", font=('Segoe UI', 10),
                          width=3, relief='raised', bd=1,
                          bg='#3498db', fg='white', activebackground='#2980b9',
                          command=lambda idx=i: self._choose_color(idx))
            btn.pack(side='right', padx=(5, 0))
    
    def _update_preview(self, idx: int):
        """Обновляет превью цвета"""
        color = self.entries[idx].get().strip()
        normalized = ColorUtility.normalize_color(color)
        
        if ColorUtility.is_valid_color(normalized):
            self.previews[idx].config(bg=normalized)
            # Обновляем цвет рамки в зависимости от яркости
            rgb = ImageColor.getrgb(normalized)
            luminance = ColorUtility.relative_luminance(rgb)
            border_color = '#2c3e50' if luminance > 0.5 else '#ecf0f1'
            self.previews[idx].config(highlightbackground=border_color)
        else:
            self.previews[idx].config(bg='#ffffff', highlightbackground='#bdc3c7')
    
    def _choose_color(self, idx: int):
        """Открывает диалог выбора цвета"""
        color_code = colorchooser.askcolor(title="Выберите цвет", 
                                          initialcolor=self.previews[idx].cget('bg'))
        if color_code[1]:
            self.entries[idx].delete(0, tk.END)
            self.entries[idx].insert(0, color_code[1])
            self.previews[idx].config(bg=color_code[1])
    
    def get_colors(self) -> List[str]:
        """Возвращает список введенных цветов"""
        return [entry.get().strip() for entry in self.entries if entry.get().strip()]
    
    def set_colors(self, colors: List[str]):
        """Устанавливает цвета"""
        for i, color in enumerate(colors):
            if i < len(self.entries):
                self.entries[i].delete(0, tk.END)
                self.entries[i].insert(0, color)
                self._update_preview(i)
    
    def update_preview_colors(self, colors: List[str]):
        """Обновляет превью с новыми цветами"""
        for i, color in enumerate(colors):
            if i < len(self.previews):
                self.previews[i].config(bg=color)
                # Обновляем рамку
                if ColorUtility.is_valid_color(color):
                    rgb = ImageColor.getrgb(color)
                    luminance = ColorUtility.relative_luminance(rgb)
                    border_color = '#2c3e50' if luminance > 0.5 else '#ecf0f1'
                    self.previews[i].config(highlightbackground=border_color)


# ============================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ С ХУДОЖЕСТВЕННЫМ ДИЗАЙНОМ
# ============================================================================

class ColorRecolorApp:
    """Главное приложение для перекраски цветов с художественным дизайном"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎨 Color Alchemist - Мастерская цветовых трансформаций")
        
        # Настраиваем стиль
        self._setup_styles()
        
        # Устанавливаем тему
        self.root.configure(bg='#2c3e50')
        self.root.geometry("1300x950")  # Увеличил высоту для лучшего отображения
        
        # Восстанавливаем стандартное поведение окна
        self.root.resizable(True, True)  # Разрешаем изменение размера
        self.root.minsize(1200, 800)  # Минимальный размер
        
        # Сервис для работы с цветами
        self.recolor_service = ColorRecolorService()
        
        # Переменные
        self.color_count = tk.IntVar(value=6)
        self.intensity_var = tk.DoubleVar(value=1.0)
        self.mode_var = tk.StringVar(value=RecolorMode.FULL_RECOLOR.value)
        
        # Создаем интерфейс
        self._create_ui()
        
        # Инициализация
        self.update_color_boxes()
        self.root.after(100, self._load_example_data)
    
    def _setup_styles(self):
        """Настраивает стили для виджетов"""
        style = ttk.Style()
        
        # Настраиваем тему
        style.theme_use('clam')
        
        # Стиль для кнопок
        style.configure('Artistic.TButton', 
                       font=('Segoe UI', 10, 'bold'),
                       padding=10,
                       background='#3498db',
                       foreground='white')
        
        style.map('Artistic.TButton',
                 background=[('active', '#2980b9'), ('disabled', '#bdc3c7')])
        
        # Стиль для радиокнопок
        style.configure('Artistic.TRadiobutton',
                       font=('Segoe UI', 10),
                       background='#2c3e50',
                       foreground='#ecf0f1')
    
    def _create_ui(self):
        """Создает пользовательский интерфейс с художественным дизайном"""
        # Главный контейнер с прокруткой
        canvas = tk.Canvas(self.root, bg='#2c3e50', highlightthickness=0)
        canvas.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(self.root, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')

        canvas.configure(yscrollcommand=scrollbar.set)

        main_container = StyledFrame(canvas)
        canvas.create_window((0, 0), window=main_container, anchor='nw')

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        main_container.bind("<Configure>", on_configure)

        
        # Заголовок приложения с кнопками управления окном
        header_frame = StyledFrame(main_container, bg='#34495e')
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Левая часть заголовка - название
        title_frame = StyledFrame(header_frame, bg='#34495e')
        title_frame.pack(side='left', fill='x', expand=True)
        
        title_label = tk.Label(title_frame, 
                              text="🎨 Color Alchemist", 
                              font=('Segoe UI', 24, 'bold'),
                              bg='#34495e', fg='#ecf0f1')
        title_label.pack(side='left', padx=20, pady=15)
        
        subtitle_label = tk.Label(title_frame,
                                 text="Мастерская цветовых трансформаций",
                                 font=('Segoe UI', 11, 'italic'),
                                 bg='#34495e', fg='#bdc3c7')
        subtitle_label.pack(side='left', padx=10, pady=15)
        
        # Правая часть заголовка - кнопки управления
        control_buttons_frame = StyledFrame(header_frame, bg='#34495e')
        control_buttons_frame.pack(side='right', padx=20)
        
        # Кнопка закрытия
        close_btn = tk.Button(control_buttons_frame, text="✕", 
                             font=('Segoe UI', 12, 'bold'),
                             bg='#e74c3c', fg='white',
                             activebackground='#c0392b',
                             relief='flat', bd=0,
                             width=3, height=1,
                             command=self.root.quit)
        close_btn.pack(side='left', padx=2)
        
        # Кнопка сворачивания
        minimize_btn = tk.Button(control_buttons_frame, text="—", 
                                font=('Segoe UI', 12, 'bold'),
                                bg='#3498db', fg='white',
                                activebackground='#2980b9',
                                relief='flat', bd=0,
                                width=3, height=1,
                                command=lambda: self.root.iconify())
        minimize_btn.pack(side='left', padx=2)
        
        # Кнопка справки
        help_btn = tk.Button(control_buttons_frame, text="?", 
                            font=('Segoe UI', 12, 'bold'),
                            bg='#9b59b6', fg='white',
                            activebackground='#8e44ad',
                            relief='flat', bd=0,
                            width=3, height=1,
                            command=self._show_help)
        help_btn.pack(side='left', padx=2)
        
        # Основное содержимое - две колонки как в оригинале
        main_content = StyledFrame(main_container)
        main_content.pack(fill='both', expand=True)
        
        # Панель управления сверху
        self._create_control_panel(main_content)
        
        # Две панели с цветами
        colors_frame = StyledFrame(main_content)
        colors_frame.pack(fill='both', expand=True, pady=20)
        
        # Левая колонка (светлые цвета)
        self.left_panel = ColorPaletteFrame(colors_frame, "Левая колонка (светлые цвета)", "☀️")
        self.left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Правая колонка (темные цвета)
        self.right_panel = ColorPaletteFrame(colors_frame, "Правая колонка (темные цвета)", "🌙")
        self.right_panel.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Кнопка обработки по центру
        process_frame = StyledFrame(main_content, bg='#2c3e50')
        process_frame.pack(fill='x', pady=10)
        
        self.process_btn = tk.Button(process_frame, 
                                    text="🎯 ПЕРЕКРАСИТЬ ПАЛИТРЫ",
                                    font=('Segoe UI', 12, 'bold'),
                                    bg='#e74c3c', fg='white',
                                    activebackground='#c0392b',
                                    relief='raised', bd=0,
                                    height=2,
                                    command=self.process_colors)
        self.process_btn.pack(fill='x', padx=200, pady=10)
        
        # Панель результатов (больше места для отображения)
        self._create_result_panel(main_content)
    
    def _create_control_panel(self, parent):
        """Создает художественную панель управления"""
        control_frame = StyledFrame(parent, bg='#34495e')
        control_frame.pack(fill='x', pady=(0, 15))
        
        # Внутренний фрейм
        inner_frame = StyledFrame(control_frame, bg='#2c3e50')
        inner_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Заголовок
        tk.Label(inner_frame, text="⚙️ Параметры перекраски",
                font=('Segoe UI', 12, 'bold'),
                bg='#2c3e50', fg='#ecf0f1').pack(anchor='w', pady=(0, 15))
        
        # Первая строка: количество цветов и базовый цвет
        row1_frame = StyledFrame(inner_frame, bg='#2c3e50')
        row1_frame.pack(fill='x', pady=5)
        
        # Количество цветов
        tk.Label(row1_frame, text="Количество цветов в колонке:",
                font=('Segoe UI', 10),
                bg='#2c3e50', fg='#bdc3c7').pack(side='left', padx=(0, 10))
        
        spinbox = tk.Spinbox(row1_frame, from_=1, to=10, width=8,
                            textvariable=self.color_count,
                            font=('Segoe UI', 10),
                            bg='#34495e', fg='#ecf0f1',
                            relief='flat', bd=2,
                            highlightbackground='#3498db',
                            command=self.update_color_boxes,
                            justify='center')
        spinbox.pack(side='left', padx=(0, 30))
        
        # Базовый цвет
        tk.Label(row1_frame, text="Базовый цвет для перекраски:",
                font=('Segoe UI', 10),
                bg='#2c3e50', fg='#bdc3c7').pack(side='left', padx=(0, 10))
        
        self.base_color_entry = tk.Entry(row1_frame, font=('Segoe UI', 10),
                                        width=12, relief='flat', bd=2,
                                        highlightcolor='#3498db',
                                        highlightbackground='#bdc3c7',
                                        bg='#34495e', fg='#ecf0f1')
        self.base_color_entry.insert(0, "#3498db")
        self.base_color_entry.pack(side='left', padx=(0, 10))
        self.base_color_entry.bind('<KeyRelease>', self._update_base_preview)
        
        self.base_preview = tk.Label(row1_frame, width=6, height=1,
                                     relief='ridge', borderwidth=2,
                                     bg='#3498db', cursor="hand2")
        self.base_preview.pack(side='left', padx=(0, 10))
        self.base_preview.bind("<Button-1>", lambda e: self._choose_base_color())
        
        # Кнопка выбора цвета
        tk.Button(row1_frame, text="🎨 Выбрать",
                 font=('Segoe UI', 9),
                 bg='#9b59b6', fg='white',
                 command=self._choose_base_color).pack(side='left')
        
        # Вторая строка: интенсивность
        row2_frame = StyledFrame(inner_frame, bg='#2c3e50')
        row2_frame.pack(fill='x', pady=15)
        
        tk.Label(row2_frame, text="Интенсивность перекраски:",
                font=('Segoe UI', 10),
                bg='#2c3e50', fg='#bdc3c7').pack(side='left', padx=(0, 15))
        
        self.intensity_label = tk.Label(row2_frame, 
                                       text="1.0",
                                       font=('Segoe UI', 10, 'bold'),
                                       bg='#2c3e50', fg='#3498db',
                                       width=4)
        self.intensity_label.pack(side='right', padx=(10, 0))
        
        slider = ttk.Scale(row2_frame, from_=0, to=1,
                          variable=self.intensity_var,
                          orient="horizontal",
                          length=200)
        slider.pack(side='right', fill='x', expand=True)
        slider.bind('<Motion>', lambda e: self._update_intensity_label())
        
        # Третья строка: режимы
        row3_frame = StyledFrame(inner_frame, bg='#2c3e50')
        row3_frame.pack(fill='x', pady=15)
        
        tk.Label(row3_frame, text="Режим перекраски:",
                font=('Segoe UI', 10),
                bg='#2c3e50', fg='#bdc3c7').pack(side='left', padx=(0, 15))
        
        # Создаем художественные радиокнопки
        modes_frame = StyledFrame(row3_frame, bg='#2c3e50')
        modes_frame.pack(side='left', fill='x', expand=True)
        
        modes = [
            ("🌓 Сохранить оттенки", RecolorMode.KEEP_HUE.value),
            ("🎭 Полная перекраска", RecolorMode.FULL_RECOLOR.value),
            ("🌈 Смешанный режим", RecolorMode.MIXED.value)
        ]
        
        for text, value in modes:
            rb = tk.Radiobutton(modes_frame, text=text,
                               variable=self.mode_var,
                               value=value,
                               font=('Segoe UI', 10),
                               bg='#2c3e50', fg='#ecf0f1',
                               activebackground='#2c3e50',
                               selectcolor='#3498db')
            rb.pack(side='left', padx=20)
        
        # Кнопка обновления
        tk.Button(row3_frame, text="🔄 Обновить колонки",
                 font=('Segoe UI', 9),
                 bg='#27ae60', fg='white',
                 command=self.update_color_boxes).pack(side='right')
    
    def _create_result_panel(self, parent):
        """Создает художественную панель результатов с увеличенной областью"""
        result_frame = StyledFrame(parent, bg='#34495e')
        result_frame.pack(fill='both', expand=True)
        
        # Заголовок с кнопками управления результатами
        header_frame = StyledFrame(result_frame, bg='#2c3e50')
        header_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(header_frame, text="📊 Результаты перекраски", 
                font=('Segoe UI', 12, 'bold'),
                bg='#2c3e50', fg='#ecf0f1').pack(side='left', padx=15, pady=10)
        
        # Кнопки управления результатами
        buttons_frame = StyledFrame(header_frame, bg='#2c3e50')
        buttons_frame.pack(side='right', padx=15)
        
        tk.Button(buttons_frame, text="📋 Копировать",
                 font=('Segoe UI', 9),
                 bg='#27ae60', fg='white',
                 command=self._copy_all_results).pack(side='left', padx=2)
        
        tk.Button(buttons_frame, text="🗑️ Очистить",
                 font=('Segoe UI', 9),
                 bg='#e74c3c', fg='white',
                 command=lambda: self.result_text.delete(1.0, tk.END)).pack(side='left', padx=2)
        
        tk.Button(buttons_frame, text="📁 Экспорт",
                 font=('Segoe UI', 9),
                 bg='#3498db', fg='white',
                 command=self._export_results).pack(side='left', padx=2)
        
        tk.Button(buttons_frame, text="ℹ️ Справка",
                 font=('Segoe UI', 9),
                 bg='#9b59b6', fg='white',
                 command=self._show_results_help).pack(side='left', padx=2)
        
        # Текстовое поле с прокруткой (увеличено для лучшего отображения)
        text_container = StyledFrame(result_frame, bg='#2c3e50')
        text_container.pack(fill='both', expand=True, padx=2, pady=(0, 2))
        
        # Фрейм для текста и прокрутки
        text_inner_frame = StyledFrame(text_container, bg='#2c3e50')
        text_inner_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Создаем текстовое поле и скроллбар
        self.result_text = tk.Text(text_inner_frame, 
                                  font=('Consolas', 11),  # Увеличен шрифт
                                  bg='#1c2833', fg='#ecf0f1',
                                  relief='flat', bd=0,
                                  padx=20, pady=20,
                                  wrap='word',
                                  height=12)  # Установлена высота
        
        # Вертикальная прокрутка
        v_scrollbar = ttk.Scrollbar(text_inner_frame, orient='vertical')
        v_scrollbar.pack(side='right', fill='y')
        
        # Горизонтальная прокрутка
        h_scrollbar = ttk.Scrollbar(text_inner_frame, orient='horizontal')
        h_scrollbar.pack(side='bottom', fill='x')
        
        self.result_text.pack(side='left', fill='both', expand=True)
        
        # Настраиваем прокрутки
        self.result_text.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self.result_text.yview)
        self.result_text.config(xscrollcommand=h_scrollbar.set)
        h_scrollbar.config(command=self.result_text.xview)
        
        # Контекстное меню
        ContextMenuMixin.add_context_menu(self.result_text)
        
        # Настраиваем теги для форматирования текста
        self._setup_text_tags()
        
        # Кнопки внизу панели результатов
        bottom_buttons = StyledFrame(result_frame, bg='#2c3e50')
        bottom_buttons.pack(fill='x', pady=10)
        
        tk.Button(bottom_buttons, text="🔄 Загрузить пример палитры",
                 font=('Segoe UI', 10),
                 bg='#9b59b6', fg='white',
                 command=self._load_example_data).pack(side='left', padx=10)
        
        tk.Button(bottom_buttons, text="🎨 Показать цветовую схему",
                 font=('Segoe UI', 10),
                 bg='#3498db', fg='white',
                 command=self._show_color_scheme).pack(side='left', padx=10)
        
        tk.Button(bottom_buttons, text="💾 Сохранить настройки",
                 font=('Segoe UI', 10),
                 bg='#27ae60', fg='white',
                 command=self._save_settings).pack(side='left', padx=10)
    
    def _setup_text_tags(self):
        """Настраивает теги для форматирования текста в результатах"""
        # Основные теги
        self.result_text.tag_config('header', 
                                   font=('Consolas', 12, 'bold'), 
                                   foreground='#3498db',
                                   spacing1=10, spacing3=5)
        
        self.result_text.tag_config('subheader', 
                                   font=('Consolas', 11, 'bold'), 
                                   foreground='#9b59b6',
                                   spacing1=8)
        
        self.result_text.tag_config('bold', 
                                   font=('Consolas', 11, 'bold'))
        
        self.result_text.tag_config('original', 
                                   font=('Consolas', 11),
                                   foreground='#e74c3c')
        
        self.result_text.tag_config('new', 
                                   font=('Consolas', 11, 'bold'),
                                   foreground='#27ae60')
        
        self.result_text.tag_config('arrow', 
                                   font=('Consolas', 11),
                                   foreground='#f1c40f')
        
        self.result_text.tag_config('luminance', 
                                   font=('Consolas', 10),
                                   foreground='#95a5a6')
        
        self.result_text.tag_config('summary', 
                                   font=('Consolas', 11, 'bold'),
                                   foreground='#f1c40f',
                                   spacing1=10)
        
        self.result_text.tag_config('separator', 
                                   font=('Consolas', 10),
                                   foreground='#7f8c8d')
        
        self.result_text.tag_config('success', 
                                   font=('Consolas', 11, 'bold'),
                                   foreground='#27ae60',
                                   spacing1=10)
        
        self.result_text.tag_config('error', 
                                   font=('Consolas', 11, 'bold'),
                                   foreground='#e74c3c')
    
    def _update_intensity_label(self):
        """Обновляет метку интенсивности"""
        intensity = self.intensity_var.get()
        self.intensity_label.config(text=f"{intensity:.2f}")
    
    def _choose_base_color(self):
        """Выбирает базовый цвет"""
        color_code = colorchooser.askcolor(title="Выберите базовый цвет",
                                          initialcolor=self.base_preview.cget('bg'))
        if color_code[1]:
            self.base_color_entry.delete(0, tk.END)
            self.base_color_entry.insert(0, color_code[1])
            self.base_preview.config(bg=color_code[1])
    
    def _update_base_preview(self, event=None):
        """Обновляет превью базового цвета"""
        color = self.base_color_entry.get().strip()
        normalized = ColorUtility.normalize_color(color)
        
        if ColorUtility.is_valid_color(normalized):
            self.base_preview.config(bg=normalized)
        else:
            self.base_preview.config(bg='#ffffff')
    
    def update_color_boxes(self):
        """Обновляет количество полей для цветов в обеих колонках"""
        count = self.color_count.get()
        self.left_panel.create_color_inputs(count)
        self.right_panel.create_color_inputs(count)
    
    def process_colors(self):
        """Обрабатывает цвета из обеих колонок"""
        base_color = self.base_color_entry.get()
        normalized_base = ColorUtility.normalize_color(base_color)
        
        if not ColorUtility.is_valid_color(normalized_base):
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "❌ Ошибка: неверный базовый цвет\n", 'error')
            self.result_text.insert(tk.END, "Пожалуйста, введите корректный HEX-код цвета (например, #3498db)\n")
            return
        
        # Анимация кнопки
        original_text = self.process_btn.cget('text')
        original_bg = self.process_btn.cget('bg')
        self.process_btn.config(text="✨ Обработка...", bg='#f39c12', state='disabled')
        self.root.update()
        
        try:
            # Получаем входные данные из ОБЕИХ колонок
            left_colors = self.left_panel.get_colors()
            right_colors = self.right_panel.get_colors()
            
            intensity = self.intensity_var.get()
            mode = RecolorMode(self.mode_var.get())
            
            # Обрабатываем цвета из обеих колонок
            left_results = self.recolor_service.recolor_palette(
                left_colors, normalized_base, intensity, mode
            )
            
            right_results = self.recolor_service.recolor_palette(
                right_colors, normalized_base, intensity, mode
            )
            
            # Отображаем результаты
            self._display_results(left_results, right_results)
            
            # Обновляем превью в обеих колонках
            left_new_colors = [r.new_color for r in left_results]
            right_new_colors = [r.new_color for r in right_results]
            
            self.left_panel.update_preview_colors(left_new_colors)
            self.right_panel.update_preview_colors(right_new_colors)
            
        except Exception as e:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"❌ Ошибка при обработке цветов:\n", 'error')
            self.result_text.insert(tk.END, f"{str(e)}\n")
        finally:
            # Восстанавливаем кнопку
            self.process_btn.config(text=original_text, bg=original_bg, state='normal')
    
    def _display_results(self, left_results: List[ColorResult], 
                        right_results: List[ColorResult]):
        """Отображает результаты обработки из обеих колонок"""
        self.result_text.delete(1.0, tk.END)
        
        if not left_results and not right_results:
            self.result_text.insert(tk.END, "ℹ️ Нет данных для отображения\n", 'header')
            self.result_text.insert(tk.END, "Введите цвета в левую и/или правую колонку и нажмите 'Перекрасить палитры'\n")
            return
        
        # Заголовок
        self.result_text.insert(tk.END, "🎨 РЕЗУЛЬТАТЫ ЦВЕТОВОЙ ПЕРЕКРАСКИ\n", 'header')
        self.result_text.insert(tk.END, "=" * 70 + "\n", 'separator')
        self.result_text.insert(tk.END, f"Базовый цвет: {self.base_color_entry.get()}\n")
        self.result_text.insert(tk.END, f"Интенсивность: {self.intensity_var.get():.2f}\n")
        self.result_text.insert(tk.END, f"Режим: {self.mode_var.get().replace('_', ' ').title()}\n\n")
        
        total_processed = len(left_results) + len(right_results)
        
        # Левая колонка
        if left_results:
            self.result_text.insert(tk.END, "☀️ ЛЕВАЯ КОЛОНКА (СВЕТЛЫЕ ЦВЕТА):\n", 'subheader')
            self.result_text.insert(tk.END, "-" * 50 + "\n", 'separator')
            
            for i, result in enumerate(left_results, 1):
                self.result_text.insert(tk.END, f"{i:2d}. ", 'bold')
                self.result_text.insert(tk.END, f"{result.original:12s}", 'original')
                self.result_text.insert(tk.END, "  →  ", 'arrow')
                self.result_text.insert(tk.END, f"{result.new_color:12s}", 'new')
                
                # Индикатор яркости с цветовым кодом
                lum_display = f"{result.luminance:.3f}"
                if result.luminance > 0.7:
                    lum_indicator = "🔆 Светлый"
                elif result.luminance < 0.3:
                    lum_indicator = "🔅 Тёмный"
                else:
                    lum_indicator = "💡 Средний"
                
                self.result_text.insert(tk.END, f"   {lum_indicator} (яркость: {lum_display})\n")
            
            self.result_text.insert(tk.END, "\n")
        
        # Правая колонка
        if right_results:
            self.result_text.insert(tk.END, "🌙 ПРАВАЯ КОЛОНКА (ТЕМНЫЕ ЦВЕТА):\n", 'subheader')
            self.result_text.insert(tk.END, "-" * 50 + "\n", 'separator')
            
            for i, result in enumerate(right_results, 1):
                self.result_text.insert(tk.END, f"{i:2d}. ", 'bold')
                self.result_text.insert(tk.END, f"{result.original:12s}", 'original')
                self.result_text.insert(tk.END, "  →  ", 'arrow')
                self.result_text.insert(tk.END, f"{result.new_color:12s}", 'new')
                
                # Индикатор яркости с цветовым кодом
                lum_display = f"{result.luminance:.3f}"
                if result.luminance > 0.7:
                    lum_indicator = "🔆 Светлый"
                elif result.luminance < 0.3:
                    lum_indicator = "🔅 Тёмный"
                else:
                    lum_indicator = "💡 Средний"
                
                self.result_text.insert(tk.END, f"   {lum_indicator} (яркость: {lum_display})\n")
        
        # Сводка
        total_left = len(left_results)
        total_right = len(right_results)
        
        self.result_text.insert(tk.END, "\n" + "=" * 70 + "\n", 'separator')
        self.result_text.insert(tk.END, "📊 СВОДКА РЕЗУЛЬТАТОВ:\n", 'summary')
        self.result_text.insert(tk.END, f"• Всего обработано цветов: {total_processed}\n")
        self.result_text.insert(tk.END, f"• Левая колонка: {total_left} цветов\n")
        self.result_text.insert(tk.END, f"• Правая колонка: {total_right} цветов\n")
        
        # Подсказка
        self.result_text.insert(tk.END, "\n💡 Новые цвета отображены в превью соответствующих колонок\n", 'success')
        self.result_text.insert(tk.END, "💡 Используйте правую кнопку мыши для копирования текста\n")
        
        # Прокручиваем к началу
        self.result_text.see(1.0)
    
    def _copy_all_results(self):
        """Копирует все результаты в буфер обмена"""
        content = self.result_text.get(1.0, tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("Успех", "Результаты скопированы в буфер обмена")
    
    def _export_results(self):
        """Экспортирует результаты"""
        content = self.result_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Нет данных", "Нет данных для экспорта")
            return
        
        # В реальном приложении здесь была бы логика сохранения в файл
        messagebox.showinfo("Экспорт", 
                          "Функция экспорта в разработке\n\n"
                          f"Готово для экспорта: {len(content)} символов\n"
                          "В реальном приложении здесь будет диалог сохранения файла")
    
    def _show_help(self):
        """Показывает справку по приложению"""
        help_text = """
🎨 Color Alchemist - Помощь

1. ВВОД ЦВЕТОВ:
   • Введите HEX-коды цветов в поля (например, #3498db)
   • Или нажмите кнопку 🖌️ для выбора цвета
   • Можно использовать форматы: #RGB, #RRGGBB

2. НАСТРОЙКИ:
   • Количество цветов: сколько цветов в каждой колонке
   • Базовый цвет: цвет, к которому будет выполнена перекраска
   • Интенсивность: сила перекраски (0-1)
   • Режим: способ перекраски цветов

3. РЕЖИМЫ:
   • Сохранить оттенки: сохраняет исходные оттенки
   • Полная перекраска: полностью меняет цвета на базовый
   • Смешанный режим: комбинация обоих подходов

4. РЕЗУЛЬТАТЫ:
   • Отображаются в нижней панели
   • Новые цвета показываются в превью колонок
   • Можно копировать текст (ПКМ → Копировать)
"""
        messagebox.showinfo("Справка - Color Alchemist", help_text)
    
    def _show_results_help(self):
        """Показывает справку по результатам"""
        help_text = """
📊 Помощь по результатам:

ЦВЕТОВАЯ СХЕМА ТЕКСТА:
• 🔴 Красный: Исходный цвет
• 🟢 Зеленый: Новый цвет после перекраски
• 🟡 Желтый: Стрелка преобразования
• 🔵 Синий: Заголовки и разделы
• ⚪ Серый: Дополнительная информация

ИНДИКАТОРЫ ЯРКОСТИ:
• 🔆 Светлый: Яркость > 0.7
• 💡 Средний: Яркость 0.3-0.7
• 🔅 Тёмный: Яркость < 0.3

УПРАВЛЕНИЕ:
• Прокрутка: Используйте полосы прокрутки справа и снизу
• Копирование: Правой кнопкой мыши → Копировать
• Выделение: Перетащите мышью для выделения текста
"""
        messagebox.showinfo("Справка - Результаты", help_text)
    
    def _show_color_scheme(self):
        """Показывает текущую цветовую схему"""
        scheme_text = """
🎨 ТЕКУЩАЯ ЦВЕТОВАЯ СХЕМА:

ОСНОВНЫЕ ЦВЕТА:
• Фон приложения: #2c3e50 (Тёмно-синий)
• Фон панелей: #34495e (Сине-серый)
• Текст: #ecf0f1 (Светло-серый)
• Второстепенный текст: #bdc3c7 (Серый)

АКЦЕНТНЫЕ ЦВЕТА:
• Основной акцент: #3498db (Синий)
• Успех: #27ae60 (Зеленый)
• Ошибка: #e74c3c (Красный)
• Предупреждение: #f39c12 (Оранжевый)
• Особый: #9b59b6 (Фиолетовый)

ИНТЕРФЕЙС:
• Поля ввода: #f8f9fa (Очень светлый серый)
• Рамки: #bdc3c7 (Серый)
• Активные элементы: #3498db (Синий)
"""
        messagebox.showinfo("Цветовая схема", scheme_text)
    
    def _save_settings(self):
        """Сохраняет текущие настройки"""
        settings = {
            'color_count': self.color_count.get(),
            'base_color': self.base_color_entry.get(),
            'intensity': self.intensity_var.get(),
            'mode': self.mode_var.get()
        }
        
        messagebox.showinfo("Сохранение настроек", 
                          "Функция сохранения настроек в разработке\n\n"
                          f"Текущие настройки:\n"
                          f"• Цветов в колонке: {settings['color_count']}\n"
                          f"• Базовый цвет: {settings['base_color']}\n"
                          f"• Интенсивность: {settings['intensity']:.2f}\n"
                          f"• Режим: {settings['mode'].replace('_', ' ').title()}")
    
    def _load_example_data(self):
        """Загружает примеры цветов в обе колонки"""
        # Примеры для левой колонки (светлые цвета)
        left_example_colors = [
            "#FFEAA7", "#81ECEC", "#FFC8C8", "#D8BFD8",
            "#B5EAD7", "#C7CEEA", "#FFDAC1", "#E2F0CB"
        ]
        
        # Примеры для правой колонки (темные цвета)
        right_example_colors = [
            "#D63031", "#0984E3", "#00B894", "#FD79A8",
            "#6C5CE7", "#FDCB6E", "#636E72", "#2D3436"
        ]
        
        count = min(self.color_count.get(), 8)
        
        # Устанавливаем цвета в левую колонку
        left_colors_to_set = left_example_colors[:count]
        self.left_panel.set_colors(left_colors_to_set)
        
        # Устанавливаем цвета в правую колонку
        right_colors_to_set = right_example_colors[:count]
        self.right_panel.set_colors(right_colors_to_set)
        
        # Устанавливаем интересный базовый цвет
        self.base_color_entry.delete(0, tk.END)
        self.base_color_entry.insert(0, "#9b59b6")
        self._update_base_preview()
        
        # Показываем сообщение
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "✅ Пример палитры загружен!\n\n", 'success')
        self.result_text.insert(tk.END, f"• Левая колонка: {count} светлых цветов\n")
        self.result_text.insert(tk.END, f"• Правая колонка: {count} темных цветов\n")
        self.result_text.insert(tk.END, f"• Базовый цвет: #9b59b6 (фиолетовый)\n\n")
        self.result_text.insert(tk.END, "Нажмите '🎯 ПЕРЕКРАСИТЬ ПАЛИТРЫ' для обработки\n")


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

def main():
    """Главная функция приложения"""
    root = tk.Tk()
    
    # Центрируем окно
    window_width = 1300
    window_height = 950
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2) - 50
    
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Создаем приложение
    app = ColorRecolorApp(root)
    
    # Запускаем главный цикл
    root.mainloop()


if __name__ == "__main__":
    main()