🎨 Color_nedo_hunt

A color transformation workshop for designers and color enthusiasts

Color_nedo_hunt is an interactive tool for recoloring color palettes with instant visual results. It allows you to experiment with shades, intensity, and recoloring styles right in a beautiful, stylized interface.

⚡ Features

Dynamic intensity slider: change the strength of the recoloring and see the result immediately.

Three recoloring modes:

Keep shades

Full recoloring

Mixed mode

Live preview: colors are updated automatically without unnecessary clicks.

Stylized for design and drawing: convenient columns, previews, icons, and text highlighting.

Work with HEX and color palettes: support for #RGB and #RRGGBB.

Context menu and copying: RMB → Copy, Paste, Select All.

Real-time results: brightness indicators, conversion arrows, summary.

🛠 Installation

Clone the repository:

git clone https://github.com/zaxa651/Color_nedo_hunt
cd Color_nedo_hunt


Install dependencies (Python 3.8+):

pip install pillow numpy

🚀 Launch
python Color_nedo_hunt.py


The application window will open with two columns for colors, an intensity slider, and a recolor button.

🖌 Usage

Enter HEX codes in the fields or select colors via the selection dialog.

Configure:

Number of colors

Base color

Intensity

Recolor mode

See the results in real time or click the “Recolor palettes” button.

Copy the results or export them for further work.

📊 Interface and indicators

🔆 Light: brightness > 0.7

💡 Medium: 0.3 ≤ brightness ≤ 0.7

🔅 Dark: brightness < 0.3

🔴 Original color

🟢 New color

🟡 Conversion arrow

🧩 Notes

Only valid HEX codes (#RGB or #RRGGBB) are supported.

Use vertical scrolling for large palettes.

The program is completely local, no data is sent to the internet.

💡 Planned improvements

Export to file (CSV, PNG, PDF).

Saving user settings.

Additional filters and blending modes.

📜 License

MIT License — take it, repaint it, destroy the reality of colors ;)
