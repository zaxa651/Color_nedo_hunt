import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import ImageColor
import numpy as np
import re
import colorsys

def relative_luminance(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    r = r / 12.92 if r <= 0.04045 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.04045 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.04045 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def normalize_color(color):
    if not color:
        return color
    color = color.strip().lower()
    cyrillic_to_latin = {
        'а': 'a', 'в': 'b', 'с': 'c', 'е': 'e', 'к': 'k', 'м': 'm', 'о': 'o',
        'р': 'p', 'т': 't', 'х': 'x', 'у': 'y', 'ё': 'e', 'ъ': '', 'ь': '',
        'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    for cyr, lat in cyrillic_to_latin.items():
        color = color.replace(cyr, lat)
    color = re.sub(r'[^0-9a-f#]', '', color)
    if color.startswith('#'):
        if len(color) == 4:  # #rgb -> #rrggbb
            color = '#' + color[1]*2 + color[2]*2 + color[3]*2
        return color.lower()
    if len(color) == 3:  # rgb -> #rrggbb
        return '#' + color[0]*2 + color[1]*2 + color[2]*2
    if len(color) == 6:  # rrggbb -> #rrggbb
        return '#' + color
    return color

def is_valid_color(color):
    if not color or not color.strip():
        return False
    color = normalize_color(color)
    if not color:
        return False
    try:
        ImageColor.getrgb(color)
        return True
    except ValueError:
        return False

def recolor_palette(orig_colors, target_base, intensity, mode):
    valid_colors = [normalize_color(c) for c in orig_colors if is_valid_color(c)]
    if not valid_colors:
        return [], []

    target_rgb = np.array(ImageColor.getrgb(target_base)) / 255.0
    target_h, target_l, target_s = colorsys.rgb_to_hls(*target_rgb)
    
    # Вычисляем яркость целевого цвета
    target_luminance = relative_luminance(ImageColor.getrgb(target_base))

    new_colors = []
    luminances = []

    # Собираем исходные яркости
    orig_luminances = []
    for c in valid_colors:
        orig_luminances.append(relative_luminance(ImageColor.getrgb(c)))

    # Нормализуем яркости относительно диапазона исходных яркостей
    min_orig_lum = min(orig_luminances)
    max_orig_lum = max(orig_luminances)
    
    for i, c in enumerate(valid_colors):
        rgb = np.array(ImageColor.getrgb(c)) / 255.0
        orig_h, orig_l, orig_s = colorsys.rgb_to_hls(*rgb)
        orig_lum = orig_luminances[i]
        
        if mode == "keep_hue":
            # Сохраняем исходный оттенок, но адаптируем к целевому цвету
            new_h = orig_h
            # Сохраняем относительную яркость в диапазоне целевого цвета
            if max_orig_lum != min_orig_lum:
                lum_ratio = (orig_lum - min_orig_lum) / (max_orig_lum - min_orig_lum)
                # Применяем этот ratio к диапазону яркостей
                new_l = 0.2 + 0.7 * lum_ratio  # Диапазон от 0.2 до 0.9
            else:
                new_l = target_l
            
            # Насыщенность на основе целевого цвета и исходной насыщенности
            new_s = target_s * 0.7 + orig_s * 0.3
            
        elif mode == "full_recolor":
            # Полная перекраска - берем оттенок целевого цвета
            new_h = target_h
            
            # Сохраняем относительную яркость исходных цветов
            if max_orig_lum != min_orig_lum:
                lum_ratio = (orig_lum - min_orig_lum) / (max_orig_lum - min_orig_lum)
                # Корректируем яркость для лучшего визуального результата
                if max_orig_lum > 0.7:  # Светлая палитра
                    new_l = 0.5 + 0.4 * lum_ratio
                else:  # Темная палитра
                    new_l = 0.2 + 0.5 * lum_ratio
            else:
                new_l = 0.5
                
            # Насыщенность на основе целевого цвета
            new_s = target_s * (0.8 + 0.2 * (1 - orig_lum))
            
        else:  # mixed mode
            # Смешиваем оттенки
            new_h = orig_h * (1 - intensity) + target_h * intensity
            
            # Сохраняем относительную яркость
            if max_orig_lum != min_orig_lum:
                lum_ratio = (orig_lum - min_orig_lum) / (max_orig_lum - min_orig_lum)
                new_l = orig_l * (1 - intensity) + (0.3 + 0.6 * lum_ratio) * intensity
            else:
                new_l = orig_l * (1 - intensity) + target_l * intensity
                
            new_s = orig_s * (1 - intensity) + target_s * intensity

        # Применяем интенсивность ко всем режимам
        if intensity < 1.0 and mode != "mixed":
            # Смешиваем с исходным цветом
            mix_factor = 1 - intensity
            new_h = orig_h * mix_factor + new_h * intensity
            new_s = orig_s * mix_factor + new_s * intensity
            if max_orig_lum != min_orig_lum:
                new_l = orig_l * mix_factor + new_l * intensity

        # Ограничиваем значения
        new_h = max(0.0, min(1.0, new_h))
        new_s = max(0.1, min(1.0, new_s))  # Минимальная насыщенность 0.1
        new_l = max(0.1, min(0.95, new_l))  # Ограничиваем диапазон яркости

        new_rgb = colorsys.hls_to_rgb(new_h, new_l, new_s)
        new_rgb = tuple(int(round(x * 255)) for x in new_rgb)

        new_color_hex = "#{:02x}{:02x}{:02x}".format(*new_rgb)
        new_colors.append(new_color_hex)
        luminances.append(relative_luminance(new_rgb))

    return new_colors, luminances

# Функции для контекстного меню (копирование/вставка)
def make_context_menu(widget):
    context_menu = tk.Menu(widget, tearoff=0)
    context_menu.add_command(label="Копировать", command=lambda: widget.event_generate('<<Copy>>'))
    context_menu.add_command(label="Вставить", command=lambda: widget.event_generate('<<Paste>>'))
    context_menu.add_command(label="Вырезать", command=lambda: widget.event_generate('<<Cut>>'))
    context_menu.add_separator()
    context_menu.add_command(label="Выделить все", command=lambda: widget.select_range(0, tk.END))
    
    def show_context_menu(event):
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    widget.bind("<Button-3>", show_context_menu)  # Правая кнопка мыши
    return context_menu

def update_color_boxes():
    num_colors = color_count.get()
    for widget in left_color_frame.winfo_children():
        widget.destroy()
    for widget in right_color_frame.winfo_children():
        widget.destroy()

    left_entries.clear()
    right_entries.clear()
    left_previews.clear()
    right_previews.clear()

    for i in range(num_colors):
        # Левая колонка
        left_frame = tk.Frame(left_color_frame)
        left_frame.pack(fill='x', pady=2)

        left_entry = tk.Entry(left_frame, width=10)
        left_entry.pack(side='left', padx=5)
        left_entry.bind('<KeyRelease>', lambda e, idx=i, side='left': update_preview(e, idx, side))
        make_context_menu(left_entry)  # Добавляем контекстное меню
        left_entries.append(left_entry)

        left_color_btn = tk.Button(left_frame, text="Выбрать", width=8,
                                   command=lambda idx=i, side='left': choose_color(idx, side))
        left_color_btn.pack(side='left', padx=5)

        left_preview = tk.Label(left_frame, width=4, height=1, relief='solid', borderwidth=1, bg='white')
        left_preview.pack(side='left', padx=5)
        left_previews.append(left_preview)

        # Правая колонка
        right_frame = tk.Frame(right_color_frame)
        right_frame.pack(fill='x', pady=2)

        right_entry = tk.Entry(right_frame, width=10)
        right_entry.pack(side='left', padx=5)
        right_entry.bind('<KeyRelease>', lambda e, idx=i, side='right': update_preview(e, idx, side))
        make_context_menu(right_entry)  # Добавляем контекстное меню
        right_entries.append(right_entry)

        right_color_btn = tk.Button(right_frame, text="Выбрать", width=8,
                                   command=lambda idx=i, side='right': choose_color(idx, side))
        right_color_btn.pack(side='left', padx=5)

        right_preview = tk.Label(right_frame, width=4, height=1, relief='solid', borderwidth=1, bg='white')
        right_preview.pack(side='left', padx=5)
        right_previews.append(right_preview)

def choose_color(idx, side):
    color_code = colorchooser.askcolor(title="Выберите цвет")
    if color_code[1]:
        if side == 'left':
            left_entries[idx].delete(0, tk.END)
            left_entries[idx].insert(0, color_code[1])
            left_previews[idx].config(bg=color_code[1])
        else:
            right_entries[idx].delete(0, tk.END)
            right_entries[idx].insert(0, color_code[1])
            right_previews[idx].config(bg=color_code[1])

def choose_base_color():
    color_code = colorchooser.askcolor(title="Выберите базовый цвет")
    if color_code[1]:
        base_color_entry.delete(0, tk.END)
        base_color_entry.insert(0, color_code[1])
        base_color_preview.config(bg=color_code[1])

def update_preview(event, idx, side):
    if side == 'left':
        color = left_entries[idx].get().strip()
        preview = left_previews[idx]
    else:
        color = right_entries[idx].get().strip()
        preview = right_previews[idx]
    normalized_color = normalize_color(color)
    if is_valid_color(normalized_color):
        preview.config(bg=normalized_color)
    else:
        preview.config(bg='white')

def process_colors():
    base_color = base_color_entry.get()
    normalized_base_color = normalize_color(base_color)

    if not is_valid_color(normalized_base_color):
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Ошибка: неверный базовый цвет")
        return

    left_colors = [entry.get().strip() for entry in left_entries if entry.get().strip()]
    right_colors = [entry.get().strip() for entry in right_entries if entry.get().strip()]
    intensity = intensity_var.get()
    mode = mode_var.get()

    new_left_colors, lum_left = recolor_palette(left_colors, normalized_base_color, intensity, mode)
    new_right_colors, lum_right = recolor_palette(right_colors, normalized_base_color, intensity, mode)

    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Результаты для левой колонки:\n")
    for i, (orig, new, lum) in enumerate(zip(left_colors, new_left_colors, lum_left)):
        orig_normalized = normalize_color(orig)
        result_text.insert(tk.END, f"{i+1}. {orig_normalized} -> {new} (яркость: {lum:.3f})\n")
        if i < len(left_previews):
            left_previews[i].config(bg=new)

    result_text.insert(tk.END, "\nРезультаты для правой колонки:\n")
    for i, (orig, new, lum) in enumerate(zip(right_colors, new_right_colors, lum_right)):
        orig_normalized = normalize_color(orig)
        result_text.insert(tk.END, f"{i+1}. {orig_normalized} -> {new} (яркость: {lum:.3f})\n")
        if i < len(right_previews):
            right_previews[i].config(bg=new)

def update_base_preview(event):
    color = base_color_entry.get().strip()
    normalized_color = normalize_color(color)
    if is_valid_color(normalized_color):
        base_color_preview.config(bg=normalized_color)
    else:
        base_color_preview.config(bg='white')

# === Интерфейс ===
root = tk.Tk()
root.title("Перекрашивание цветов")
root.geometry("950x700")

color_count = tk.IntVar(value=6)
intensity_var = tk.DoubleVar(value=1.0)
mode_var = tk.StringVar(value="full_recolor")

left_entries = []
right_entries = []
left_previews = []
right_previews = []

control_frame = tk.Frame(root)
control_frame.pack(pady=10)

tk.Label(control_frame, text="Количество цветов:").grid(row=0, column=0, padx=5)
color_spinbox = tk.Spinbox(control_frame, from_=1, to=10, width=5, textvariable=color_count,
                          command=update_color_boxes)
color_spinbox.grid(row=0, column=1, padx=5)
make_context_menu(color_spinbox)  # Добавляем контекстное меню для спинбокса

tk.Label(control_frame, text="Базовый цвет:").grid(row=0, column=2, padx=5)
base_color_entry = tk.Entry(control_frame, width=10)
base_color_entry.insert(0,"")
base_color_entry.grid(row=0, column=3, padx=5)
base_color_entry.bind('<KeyRelease>', update_base_preview)
make_context_menu(base_color_entry)  # Добавляем контекстное меню для базового цвета

base_color_btn = tk.Button(control_frame, text="Выбрать", command=choose_base_color)
base_color_btn.grid(row=0, column=4, padx=5)

base_color_preview = tk.Label(control_frame, width=4, height=1, relief='solid', borderwidth=1, bg="#3f95a3")
base_color_preview.grid(row=0, column=5, padx=5)

# === Ползунок интенсивности ===
tk.Label(control_frame, text="Интенсивность:").grid(row=1, column=0, padx=5, pady=10)
intensity_slider = ttk.Scale(control_frame, from_=0, to=1, orient="horizontal", variable=intensity_var)
intensity_slider.grid(row=1, column=1, columnspan=4, sticky="we", padx=5)

# === Радиокнопки выбора режима ===
mode_frame = tk.LabelFrame(control_frame, text="Режим перекраски")
mode_frame.grid(row=2, column=0, columnspan=6, pady=10, sticky="we")

tk.Radiobutton(mode_frame, text="Сохранять оттенки", variable=mode_var, value="keep_hue").pack(side="left", padx=10)
tk.Radiobutton(mode_frame, text="Полная перекраска", variable=mode_var, value="full_recolor").pack(side="left", padx=10)
tk.Radiobutton(mode_frame, text="Смешанный режим", variable=mode_var, value="mixed").pack(side="left", padx=10)

update_btn = tk.Button(control_frame, text="Обновить цвета", command=update_color_boxes)
update_btn.grid(row=1, column=5, padx=5)

main_frame = tk.Frame(root)
main_frame.pack(fill='both', expand=True, padx=10, pady=10)

left_frame = tk.LabelFrame(main_frame, text="Левая колонка (светлые цвета)")
left_frame.pack(side='left', fill='both', expand=True, padx=5)

left_color_frame = tk.Frame(left_frame)
left_color_frame.pack(fill='both', expand=True, padx=10, pady=10)

right_frame = tk.LabelFrame(main_frame, text="Правая колонка (темные цвета)")
right_frame.pack(side='right', fill='both', expand=True, padx=5)

right_color_frame = tk.Frame(right_frame)
right_color_frame.pack(fill='both', expand=True, padx=10, pady=10)

process_btn = tk.Button(root, text="Обработать цвета", command=process_colors, height=2)
process_btn.pack(pady=10)

result_frame = tk.LabelFrame(root, text="Результаты")
result_frame.pack(fill='both', expand=True, padx=10, pady=10)

result_text = tk.Text(result_frame, height=10)
result_text.pack(fill='both', expand=True, padx=10, pady=10)
make_context_menu(result_text)  # Добавляем контекстное меню для текстового поля результатов

# Заполняем начальными данными из примера
def load_example_data():
    # Очищаем текущие данные
    for entry in left_entries + right_entries:
        entry.delete(0, tk.END)
    
    # Левая колонка (светлые цвета)
    left_example = [""]
    for i, color in enumerate(left_example):
        if i < len(left_entries):
            left_entries[i].insert(0, color)
            left_previews[i].config(bg="#" + color)
    
    # Правая колонка (темные цвета)
    right_example = [""]
    for i, color in enumerate(right_example):
        if i < len(right_entries):
            right_entries[i].insert(0, color)
            right_previews[i].config(bg="#" + color)

# Инициализация интерфейса
update_color_boxes()
# Загружаем пример данных после создания интерфейса
root.after(100, load_example_data)

root.mainloop()