"""
Video Renderer Agent
Creates MP4 videos from formatted scripts with animations and space visuals.
"""

import os
import json
import random
import math
from datetime import datetime

# We'll check for moviepy and install guidance if missing
try:
    from moviepy.editor import (
        VideoClip, TextClip, CompositeVideoClip, 
        ColorClip, ImageClip, concatenate_videoclips,
        AudioFileClip
    )
    from moviepy.video.fx.all import fadein, fadeout
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy not installed. Install with: pip install moviepy")

try:
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ Pillow not installed. Install with: pip install Pillow")


# Video settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Colors
COLORS = {
    'white': '#FFFFFF',
    'orange': '#F97316',
    'blue': '#3B82F6',
    'purple': '#8B5CF6',
    'yellow': '#FBBF24',
    'cyan': '#06B6D4',
}


def create_starfield_background(width, height, num_stars=300):
    """Generate a starfield background image."""
    # Create dark space background
    img = Image.new('RGB', (width, height), (5, 5, 15))
    draw = ImageDraw.Draw(img)
    
    # Add gradient (darker at edges)
    for y in range(height):
        # Subtle blue gradient from center
        distance_from_center = abs(y - height // 2) / (height // 2)
        blue_tint = int(15 - distance_from_center * 10)
        for x in range(0, width, 20):
            draw.rectangle([x, y, x + 20, y + 1], fill=(5, 5, max(10, blue_tint)))
    
    # Add stars of varying sizes and brightness
    for _ in range(num_stars):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        # Random star properties
        brightness = random.randint(150, 255)
        size = random.choice([1, 1, 1, 2, 2, 3])  # Mostly small stars
        
        # Slight color variation (white to blue-ish)
        r = brightness
        g = brightness
        b = min(255, brightness + random.randint(0, 30))
        
        if size == 1:
            draw.point((x, y), fill=(r, g, b))
        else:
            draw.ellipse([x - size, y - size, x + size, y + size], fill=(r, g, b))
    
    # Add a few bright "glow" stars
    for _ in range(15):
        x = random.randint(20, width - 20)
        y = random.randint(20, height - 20)
        
        # Create glow effect
        for radius in range(8, 0, -1):
            alpha = int(100 * (1 - radius / 8))
            color = (200 + alpha // 2, 200 + alpha // 2, 255)
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
    
    return np.array(img)


def create_planet(planet_type, size=200):
    """Generate a simple planet graphic."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Planet colors
    planet_colors = {
        'earth': [(34, 139, 34), (30, 144, 255), (34, 139, 34)],  # Green and blue
        'mars': [(193, 68, 14), (139, 69, 19), (160, 82, 45)],    # Reddish
        'jupiter': [(255, 200, 150), (210, 180, 140), (255, 220, 180)],  # Orange bands
        'sun': [(255, 200, 0), (255, 150, 0), (255, 100, 0)],     # Yellow-orange
        'moon': [(200, 200, 200), (169, 169, 169), (192, 192, 192)],  # Grey
        'venus': [(255, 198, 145), (218, 165, 105), (210, 180, 140)],  # Pale yellow
        'neptune': [(70, 130, 180), (100, 149, 237), (65, 105, 225)],  # Blue
        'saturn': [(210, 180, 140), (238, 232, 170), (189, 183, 107)],  # Pale gold
    }
    
    colors = planet_colors.get(planet_type, planet_colors['earth'])
    
    # Draw base circle
    center = size // 2
    radius = size // 2 - 10
    
    # Create gradient effect with bands
    for i, color in enumerate(colors):
        band_top = int(center - radius + (2 * radius / len(colors)) * i)
        band_bottom = int(center - radius + (2 * radius / len(colors)) * (i + 1))
        draw.ellipse([10, band_top, size - 10, band_bottom + radius], fill=color)
    
    # Draw the main planet circle with primary color
    draw.ellipse([10, 10, size - 10, size - 10], fill=colors[0])
    
    # Add some lighter spots for texture
    for _ in range(5):
        spot_x = random.randint(center - radius // 2, center + radius // 2)
        spot_y = random.randint(center - radius // 2, center + radius // 2)
        spot_size = random.randint(10, 30)
        lighter_color = tuple(min(255, c + 30) for c in colors[0])
        draw.ellipse([spot_x - spot_size, spot_y - spot_size, 
                      spot_x + spot_size, spot_y + spot_size], 
                     fill=lighter_color)
    
    # Add highlight (top-left shine)
    highlight_pos = (center - radius // 3, center - radius // 3)
    highlight_size = radius // 3
    for r in range(highlight_size, 0, -1):
        alpha = int(80 * (1 - r / highlight_size))
        highlight_color = (255, 255, 255, alpha)
        # Draw highlight as a separate layer
        
    # Add rings for Saturn
    if planet_type == 'saturn':
        # Simple ring representation
        ring_color = (210, 180, 140, 180)
        draw.ellipse([0, center - 10, size, center + 10], outline=(200, 180, 140), width=3)
    
    return np.array(img)


def get_text_style(text_size):
    """Get font size based on text_size parameter."""
    sizes = {
        'large': 72,
        'medium': 54,
        'small': 42
    }
    return sizes.get(text_size, 54)


def create_text_clip(text, duration, text_size='medium', text_position='center', 
                     animation='fade_in', color='white'):
    """Create an animated text clip."""
    
    fontsize = get_text_style(text_size)
    
    # Create text clip
    txt_clip = TextClip(
        text,
        fontsize=fontsize,
        color=COLORS.get(color, COLORS['white']),
        font='Arial-Bold',  # Use system font
        size=(VIDEO_WIDTH - 100, None),  # Max width with padding
        method='caption',
        align='center'
    )
    
    # Set duration
    txt_clip = txt_clip.set_duration(duration)
    
    # Position
    if text_position == 'top':
        txt_clip = txt_clip.set_position(('center', 150))
    elif text_position == 'bottom':
        txt_clip = txt_clip.set_position(('center', VIDEO_HEIGHT - 300))
    else:  # center
        txt_clip = txt_clip.set_position('center')
    
    # Apply animation
    if animation == 'fade_in':
        txt_clip = txt_clip.crossfadein(0.5)
    elif animation == 'fade_out':
        txt_clip = txt_clip.crossfadeout(0.5)
    elif animation in ['zoom_in', 'zoom_out', 'pulse']:
        # Add fade for these too (full zoom would require more complex animation)
        txt_clip = txt_clip.crossfadein(0.3)
    
    return txt_clip


def create_scene_clip(scene, bg_array):
    """Create a complete scene with background and text."""
    
    duration = scene['duration']
    
    # Create background clip from numpy array
    bg_clip = ImageClip(bg_array).set_duration(duration)
    
    # Create text clip
    txt_clip = create_text_clip(
        scene['text'],
        duration,
        scene.get('text_size', 'medium'),
        scene.get('text_position', 'center'),
        scene.get('animation', 'fade_in')
    )
    
    # Composite
    final = CompositeVideoClip([bg_clip, txt_clip], size=(VIDEO_WIDTH, VIDEO_HEIGHT))
    
    return final


def render_video(script_data, output_path):
    """Render the complete video from script data."""
    
    if not MOVIEPY_AVAILABLE or not PIL_AVAILABLE:
        print("❌ Required libraries not available")
        return None
    
    script = script_data['script']
    scenes = script['scenes']
    
    print(f"🎬 Rendering {len(scenes)} scenes...")
    
    # Generate background
    print("🌌 Generating starfield background...")
    bg_array = create_starfield_background(VIDEO_WIDTH, VIDEO_HEIGHT)
    
    # Create clips for each scene
    scene_clips = []
    for i, scene in enumerate(scenes):
        print(f"  📍 Scene {scene['scene_number']}: {scene['text'][:30]}...")
        clip = create_scene_clip(scene, bg_array)
        scene_clips.append(clip)
    
    # Concatenate all scenes
    print("🔗 Combining scenes...")
    final_video = concatenate_videoclips(scene_clips, method="compose")
    
    # Add fade in/out to entire video
    final_video = final_video.fadein(0.5).fadeout(0.5)
    
    # Export
    print(f"💾 Exporting to {output_path}...")
    final_video.write_videofile(
        output_path,
        fps=FPS,
        codec='libx264',
        audio=False,  # No audio for now
        preset='medium',
        threads=2
    )
    
    # Clean up
    final_video.close()
    for clip in scene_clips:
        clip.close()
    
    print(f"✅ Video saved: {output_path}")
    return output_path


def get_ready_scripts(scripts_dir="scripts_output"):
    """Find scripts that are ready to render."""
    if not os.path.exists(scripts_dir):
        return []
    
    ready = []
    for filename in os.listdir(scripts_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(scripts_dir, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if data.get('status') == 'ready_to_render':
                ready.append((filepath, data))
    
    return ready


def update_script_status(filepath, new_status, video_path=None):
    """Update the status of a script file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    data['status'] = new_status
    data['rendered_at'] = datetime.now().isoformat()
    if video_path:
        data['video_path'] = video_path
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def main():
    print("=" * 50)
    print("🎥 ASTRO SHORTS ENGINE - Video Renderer")
    print("=" * 50)
    print()
    
    if not MOVIEPY_AVAILABLE:
        print("❌ MoviePy is required. Install with:")
        print("   pip install moviepy")
        exit(1)
    
    if not PIL_AVAILABLE:
        print("❌ Pillow is required. Install with:")
        print("   pip install Pillow")
        exit(1)
    
    # Create output directory
    output_dir = "videos_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Find scripts ready to render
    ready_scripts = get_ready_scripts()
    print(f"📚 Found {len(ready_scripts)} scripts ready to render")
    
    if not ready_scripts:
        print("✨ No scripts to render. Run the formatter first.")
        return
    
    # Render the first ready script
    filepath, script_data = ready_scripts[0]
    topic = script_data.get('idea', {}).get('topic', 'untitled')
    
    print()
    print(f"🎬 Rendering: {topic}")
    print("-" * 40)
    
    # Generate output filename
    safe_topic = topic.lower().replace(' ', '_')[:30]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"{output_dir}/{safe_topic}_{timestamp}.mp4"
    
    # Render!
    result = render_video(script_data, output_path)
    
    if result:
        # Update script status
        update_script_status(filepath, 'rendered', output_path)
        
        print()
        print("=" * 50)
        print(f"✅ Video complete: {output_path}")
        print("🚀 Next step: YouTube upload")
        print("=" * 50)
    else:
        print("❌ Rendering failed")
        exit(1)


if __name__ == "__main__":
    main()
