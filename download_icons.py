"""
Download and convert Tabler icons to PNG format for the SIS application.
Uses svglib for SVG to image conversion.
Requires: requests, svglib, reportlab
"""

import os
import json
from pathlib import Path


def download_icons():
    """
    Download Tabler icons from GitHub and convert them to PNG.
    This creates a local icon library for the UI.
    """
    try:
        import requests
        from PIL import Image
        from io import BytesIO
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install requests svglib reportlab")
        return
    
    # Create icons directory
    icons_dir = Path("assets/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Icons to download from Tabler Icons (GitHub repository)
    # Format: (icon_name, tabler_icon_name)
    icons_to_download = [
        ("users", "users"),  # Students
        ("user", "user"),  # Single user
        ("books", "books"),  # Programs
        ("book", "book"),  # Single book
        ("building", "building"),  # Colleges
        ("settings", "settings"),  # Settings
        ("arrow-left-end-on-rectangle", "arrow-left-end-on-rectangle"),  # Logout
        ("search", "search"),  # Search
        ("plus", "plus"),  # Add new
        ("trash", "trash"),  # Delete
        ("edit", "edit"),  # Edit
        ("check", "check"),  # Confirm
        ("x", "x"),  # Cancel
    ]
    
    # GitHub raw content URL for Tabler Icons
    github_base = "https://raw.githubusercontent.com/tabler/tabler-icons/master/icons"
    theme_color = "#6d28d9"  # Your muted purple color
    
    downloaded = []
    failed = []
    
    for icon_file, icon_name in icons_to_download:
        svg_url = f"{github_base}/{icon_file}.svg"
        
        try:
            print(f"Downloading {icon_name}...", end=" ", flush=True)
            
            # Download SVG
            response = requests.get(svg_url, timeout=5)
            if response.status_code != 200:
                print(f"FAILED (404)")
                failed.append(icon_name)
                continue
            
            svg_content = response.text
            
            # Replace color in SVG with theme color
            # Tabler icons use currentColor or opacity, we'll inject color via style
            svg_content = svg_content.replace(
                'stroke="currentColor"',
                f'stroke="{theme_color}" stroke-width="1.5"'
            )
            svg_content = svg_content.replace(
                'stroke-width="2"',
                f'stroke-width="1.5"'
            )
            
            # Save temporary SVG file
            temp_svg = icons_dir / f"temp_{icon_name}.svg"
            with open(temp_svg, 'w') as f:
                f.write(svg_content)
            
            # Convert SVG to PNG at multiple sizes using svglib
            for size in [18, 22, 28, 36]:
                png_path = icons_dir / f"{icon_name}_{size}.png"
                
                try:
                    # Convert SVG to ReportLab drawing
                    drawing = svg2rlg(str(temp_svg))
                    if drawing:
                        # Scale drawing
                        drawing.width = size
                        drawing.height = size
                        
                        # Render to PNG
                        renderPM.drawToFile(drawing, str(png_path), fmt='PNG', dpi=72)
                except Exception as svg_err:
                    print(f"(size {size} failed: {svg_err})", end=" ")
            
            # Clean up temp SVG
            temp_svg.unlink(missing_ok=True)
            
            print("✓")
            downloaded.append(icon_name)
            
        except Exception as e:
            print(f"FAILED ({e})")
            failed.append(icon_name)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Downloaded: {len(downloaded)} icons")
    print(f"Failed: {len(failed)} icons")
    if failed:
        print(f"Failed icons: {', '.join(failed)}")
    print(f"Icons saved to: {icons_dir.absolute()}")
    print(f"{'='*50}")


def create_icon_manifest():
    """Create a manifest of available icons for reference."""
    icons_dir = Path("assets/icons")
    
    if not icons_dir.exists():
        print("Icons directory not found. Run download_icons() first.")
        return
    
    icons = {}
    for png_file in icons_dir.glob("*.png"):
        # Extract icon name (remove size suffix)
        name = png_file.stem.rsplit("_", 1)[0]
        if name not in icons:
            icons[name] = []
        icons[name].append(png_file.name)
    
    manifest = {
        "theme_color": "#6d28d9",
        "icons": icons,
        "usage": "Use ui.get_icon(name, size) to load icons"
    }
    
    manifest_path = icons_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Icon manifest created: {manifest_path}")


if __name__ == "__main__":
    download_icons()
    create_icon_manifest()

