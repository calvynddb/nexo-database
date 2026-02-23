"""
Create simple icon assets locally without needing to download.
This creates colored squares with basic symbols for now.
"""

from PIL import Image, ImageDraw
from pathlib import Path


def create_icon_assets():
    """Create basic icon files in assets/icons."""
    icons_dir = Path("assets/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Theme color
    theme_color = "#6d28d9"
    rgb = tuple(int(theme_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    # Icon definitions: (name, sizes)
    icons = {
        "users": [18, 22, 28, 36],
        "user": [18, 22, 28, 36],
        "books": [18, 22, 28, 36],
        "book": [18, 22, 28, 36],
        "building": [18, 22, 28, 36],
        "settings": [18, 22, 28, 36],
        "search": [18, 22, 28, 36],
        "plus": [18, 22, 28, 36],
        "trash": [18, 22, 28, 36],
        "edit": [18, 22, 28, 36],
        "check": [18, 22, 28, 36],
        "x": [18, 22, 28, 36],
        "arrow-left-end-on-rectangle": [18, 22, 28, 36],
    }
    
    for icon_name, sizes in icons.items():
        for size in sizes:
            # Create transparent image
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw simple icons based on name
            margin = max(1, size // 8)
            inner = size - 2 * margin
            
            if icon_name == "users":
                # Two circles for users
                draw.ellipse([margin, margin, margin + inner//2, margin + inner//2], outline=rgb, width=max(1, size//12))
                draw.ellipse([margin + inner//2 + margin//2, margin, size - margin, margin + inner//2], outline=rgb, width=max(1, size//12))
                draw.rectangle([margin, margin + inner//2 + margin, size - margin, size - margin], outline=rgb, width=max(1, size//12))
            elif icon_name == "user":
                # Single circle + rectangle
                draw.ellipse([margin, margin, size - margin, margin + inner//2], outline=rgb, width=max(1, size//12))
                draw.rectangle([margin, margin + inner//2 + margin, size - margin, size - margin], outline=rgb, width=max(1, size//12))
            elif icon_name == "books":
                # Three vertical lines (books)
                line_width = max(1, size // 8)
                draw.rectangle([margin, margin, margin + line_width, size - margin], fill=rgb)
                draw.rectangle([size//2 - line_width//2, margin, size//2 + line_width//2, size - margin], fill=rgb)
                draw.rectangle([size - margin - line_width, margin, size - margin, size - margin], fill=rgb)
            elif icon_name == "building":
                # Simple building shape (squares)
                draw.rectangle([margin, margin, size - margin, size - margin], outline=rgb, width=max(1, size//12))
                # Add windows
                step = inner // 3
                for i in range(2):
                    for j in range(2):
                        x = margin + step//2 + i * step
                        y = margin + step//2 + j * step
                        draw.rectangle([x - step//4, y - step//4, x + step//4, y + step//4], outline=rgb, width=1)
            elif icon_name == "settings":
                # Gear shape (circle with lines)
                center = size // 2
                radius = (size - 2*margin) // 2
                draw.ellipse([center - radius, center - radius, center + radius, center + radius], outline=rgb, width=max(1, size//12))
                # Add spokes
                for angle in range(0, 360, 90):
                    x = center + int(radius * 1.3 * __import__('math').cos(__import__('math').radians(angle)))
                    y = center + int(radius * 1.3 * __import__('math').sin(__import__('math').radians(angle)))
                    draw.line([(center, center), (x, y)], fill=rgb, width=max(1, size//12))
            elif icon_name == "search":
                # Magnifying glass (circle + line)
                radius = (size - 2*margin) // 2
                draw.ellipse([margin, margin, margin + radius*2, margin + radius*2], outline=rgb, width=max(1, size//12))
                draw.line([(margin + radius*1.7, margin + radius*1.7), (size - margin, size - margin)], fill=rgb, width=max(1, size//12))
            elif icon_name == "plus":
                # Plus sign
                center_x, center_y = size // 2, size // 2
                thickness = max(1, size // 6)
                draw.rectangle([center_x - thickness//2, margin, center_x + thickness//2, size - margin], fill=rgb)
                draw.rectangle([margin, center_y - thickness//2, size - margin, center_y + thickness//2], fill=rgb)
            elif icon_name == "trash":
                # Trash can
                draw.rectangle([margin, margin + inner//3, size - margin, size - margin], outline=rgb, width=max(1, size//12))
                draw.rectangle([margin + inner//4, margin, size - margin - inner//4, margin + inner//4], outline=rgb, width=max(1, size//12))
                draw.line([(margin + inner//3, margin + inner//3), (margin + inner//3, size - margin)], fill=rgb, width=1)
                draw.line([(size - margin - inner//3, margin + inner//3), (size - margin - inner//3, size - margin)], fill=rgb, width=1)
            elif icon_name == "edit":
                # Pencil
                draw.polygon([(size - margin, margin), (margin, size - margin), (margin, size - margin + inner//4), (size - margin + inner//4, margin)], outline=rgb, width=max(1, size//12))
            elif icon_name == "check":
                # Checkmark
                draw.line([(margin, size//2), (size//2, size - margin - 2), (size - margin, margin + 2)], fill=rgb, width=max(2, size//8))
            elif icon_name == "x":
                # X mark
                draw.line([(margin, margin), (size - margin, size - margin)], fill=rgb, width=max(2, size//8))
                draw.line([(size - margin, margin), (margin, size - margin)], fill=rgb, width=max(2, size//8))
            elif icon_name == "arrow-left-end-on-rectangle":
                # Arrow pointing left
                draw.line([(size - margin, margin), (margin + inner//4, margin), (margin + inner//4, size - margin), (size - margin, size - margin)], fill=rgb, width=max(1, size//10))
                draw.polygon([(margin + inner//4, size//2), (margin, size//2 - inner//6), (margin, size//2 + inner//6)], fill=rgb)
            
            # Save PNG
            png_path = icons_dir / f"{icon_name}_{size}.png"
            img.save(png_path)
            print(f"Created {png_path.name}")
    
    print(f"\n✓ App icons created in {icons_dir.absolute()}")


if __name__ == "__main__":
    create_icon_assets()
