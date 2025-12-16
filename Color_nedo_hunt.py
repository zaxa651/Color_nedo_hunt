"""
Инструмент для перекрашивания цветовых палитр
Применены принципы SOLID, разделение ответственности и лучшие практики
"""

import tkinter as tk
from tkinter import ttk, colorchooser
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
# GUI КОМПОНЕНТЫ
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


class ColorInputPanel:
    """Панель для ввода цветов"""
    
    def __init__(self, parent, title: str):
        self.frame = tk.LabelFrame(parent, text=title)
        self.color_frame = tk.Frame(self.frame)
        self.color_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.entries: List[tk.Entry] = []
        self.previews: List[tk.Label] = []
    
    def create_color_inputs(self, count: int):
        """Создает поля для ввода цветов"""
        # Очищаем старые виджеты
        for widget in self.color_frame.winfo_children():
            widget.destroy()
        
        self.entries.clear()
        self.previews.clear()
        
        for i in range(count):
            row_frame = tk.Frame(self.color_frame)
            row_frame.pack(fill='x', pady=2)
            
            # Поле ввода
            entry = tk.Entry(row_frame, width=10)
            entry.pack(side='left', padx=5)
            entry.bind('<KeyRelease>', lambda e, idx=i: self._update_preview(idx))
            ContextMenuMixin.add_context_menu(entry)
            self.entries.append(entry)
            
            # Кнопка выбора цвета
            btn = tk.Button(row_frame, text="Выбрать", width=8,
                          command=lambda idx=i: self._choose_color(idx))
            btn.pack(side='left', padx=5)
            
            # Превью цвета
            preview = tk.Label(row_frame, width=4, height=1, 
                             relief='solid', borderwidth=1, bg='white')
            preview.pack(side='left', padx=5)
            self.previews.append(preview)
    
    def _update_preview(self, idx: int):
        """Обновляет превью цвета"""
        color = self.entries[idx].get().strip()
        normalized = ColorUtility.normalize_color(color)
        
        if ColorUtility.is_valid_color(normalized):
            self.previews[idx].config(bg=normalized)
        else:
            self.previews[idx].config(bg='white')
    
    def _choose_color(self, idx: int):
        """Открывает диалог выбора цвета"""
        color_code = colorchooser.askcolor(title="Выберите цвет")
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
                normalized = ColorUtility.normalize_color(color)
                if ColorUtility.is_valid_color(normalized):
                    self.previews[i].config(bg=normalized)
    
    def update_preview_colors(self, colors: List[str]):
        """Обновляет превью с новыми цветами"""
        for i, color in enumerate(colors):
            if i < len(self.previews):
                self.previews[i].config(bg=color)
    
    def pack(self, **kwargs):
        """Упаковывает фрейм"""
        self.frame.pack(**kwargs)


# ============================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================================

class ColorRecolorApp:
    """Главное приложение для перекраски цветов"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Перекрашивание цветов")
        self.root.geometry("950x750")
        
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
    
    def _create_ui(self):
        """Создает пользовательский интерфейс"""
        # Панель управления
        self._create_control_panel()
        
        # Панели ввода цветов
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.left_panel = ColorInputPanel(main_frame, "Левая колонка (светлые цвета)")
        self.left_panel.pack(side='left', fill='both', expand=True, padx=5)
        
        self.right_panel = ColorInputPanel(main_frame, "Правая колонка (темные цвета)")
        self.right_panel.pack(side='right', fill='both', expand=True, padx=5)
        
        # Кнопка обработки
        process_btn = tk.Button(self.root, text="Обработать цвета", 
                               command=self.process_colors, height=2)
        process_btn.pack(pady=10)
        
        # Панель результатов
        self._create_result_panel()
    
    def _create_control_panel(self):
        """Создает панель управления"""
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        # Количество цветов
        tk.Label(control_frame, text="Количество цветов:").grid(row=0, column=0, padx=5)
        spinbox = tk.Spinbox(control_frame, from_=1, to=10, width=5,
                            textvariable=self.color_count,
                            command=self.update_color_boxes)
        spinbox.grid(row=0, column=1, padx=5)
        ContextMenuMixin.add_context_menu(spinbox)
        
        # Базовый цвет
        tk.Label(control_frame, text="Базовый цвет:").grid(row=0, column=2, padx=5)
        self.base_color_entry = tk.Entry(control_frame, width=10)
        self.base_color_entry.insert(0, "#3f95a3")
        self.base_color_entry.grid(row=0, column=3, padx=5)
        self.base_color_entry.bind('<KeyRelease>', self._update_base_preview)
        ContextMenuMixin.add_context_menu(self.base_color_entry)
        
        btn = tk.Button(control_frame, text="Выбрать", command=self._choose_base_color)
        btn.grid(row=0, column=4, padx=5)
        
        self.base_preview = tk.Label(control_frame, width=4, height=1,
                                     relief='solid', borderwidth=1, bg="#3f95a3")
        self.base_preview.grid(row=0, column=5, padx=5)
        
        # Слайдер интенсивности
        tk.Label(control_frame, text="Интенсивность:").grid(row=1, column=0, padx=5, pady=10)
        slider = ttk.Scale(control_frame, from_=0, to=1, orient="horizontal",
                          variable=self.intensity_var)
        slider.grid(row=1, column=1, columnspan=4, sticky="we", padx=5)
        
        # Радиокнопки режимов
        mode_frame = tk.LabelFrame(control_frame, text="Режим перекраски")
        mode_frame.grid(row=2, column=0, columnspan=6, pady=10, sticky="we")
        
        tk.Radiobutton(mode_frame, text="Сохранять оттенки",
                      variable=self.mode_var, 
                      value=RecolorMode.KEEP_HUE.value).pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="Полная перекраска",
                      variable=self.mode_var,
                      value=RecolorMode.FULL_RECOLOR.value).pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="Смешанный режим",
                      variable=self.mode_var,
                      value=RecolorMode.MIXED.value).pack(side="left", padx=10)
        
        # Кнопка обновления
        update_btn = tk.Button(control_frame, text="Обновить цвета",
                              command=self.update_color_boxes)
        update_btn.grid(row=1, column=5, padx=5)
    
    def _create_result_panel(self):
        """Создает панель результатов"""
        result_frame = tk.LabelFrame(self.root, text="Результаты")
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.result_text = tk.Text(result_frame, height=10)
        self.result_text.pack(fill='both', expand=True, padx=10, pady=10)
        ContextMenuMixin.add_context_menu(self.result_text)
    
    def _choose_base_color(self):
        """Выбирает базовый цвет"""
        color_code = colorchooser.askcolor(title="Выберите базовый цвет")
        if color_code[1]:
            self.base_color_entry.delete(0, tk.END)
            self.base_color_entry.insert(0, color_code[1])
            self.base_preview.config(bg=color_code[1])
    
    def _update_base_preview(self, event):
        """Обновляет превью базового цвета"""
        color = self.base_color_entry.get().strip()
        normalized = ColorUtility.normalize_color(color)
        
        if ColorUtility.is_valid_color(normalized):
            self.base_preview.config(bg=normalized)
        else:
            self.base_preview.config(bg='white')
    
    def update_color_boxes(self):
        """Обновляет количество полей для цветов"""
        count = self.color_count.get()
        self.left_panel.create_color_inputs(count)
        self.right_panel.create_color_inputs(count)
    
    def process_colors(self):
        """Обрабатывает цвета"""
        base_color = self.base_color_entry.get()
        normalized_base = ColorUtility.normalize_color(base_color)
        
        if not ColorUtility.is_valid_color(normalized_base):
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Ошибка: неверный базовый цвет")
            return
        
        # Получаем входные данные
        left_colors = self.left_panel.get_colors()
        right_colors = self.right_panel.get_colors()
        intensity = self.intensity_var.get()
        mode = RecolorMode(self.mode_var.get())
        
        # Обрабатываем цвета
        left_results = self.recolor_service.recolor_palette(
            left_colors, normalized_base, intensity, mode
        )
        right_results = self.recolor_service.recolor_palette(
            right_colors, normalized_base, intensity, mode
        )
        
        # Отображаем результаты
        self._display_results(left_results, right_results)
        
        # Обновляем превью
        self.left_panel.update_preview_colors([r.new_color for r in left_results])
        self.right_panel.update_preview_colors([r.new_color for r in right_results])
    
    def _display_results(self, left_results: List[ColorResult], 
                        right_results: List[ColorResult]):
        """Отображает результаты обработки"""
        self.result_text.delete(1.0, tk.END)
        
        self.result_text.insert(tk.END, "Результаты для левой колонки:\n")
        for i, result in enumerate(left_results, 1):
            self.result_text.insert(
                tk.END,
                f"{i}. {result.original} -> {result.new_color} "
                f"(яркость: {result.luminance:.3f})\n"
            )
        
        self.result_text.insert(tk.END, "\nРезультаты для правой колонки:\n")
        for i, result in enumerate(right_results, 1):
            self.result_text.insert(
                tk.END,
                f"{i}. {result.original} -> {result.new_color} "
                f"(яркость: {result.luminance:.3f})\n"
            )
    
    def _load_example_data(self):
        """Загружает примеры данных"""
        # Здесь можно добавить примеры, если нужно
        pass


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

def main():
    """Главная функция приложения"""
    root = tk.Tk()
    app = ColorRecolorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()