"""
Video Renderer Agent
Creates MP4 videos from formatted scripts with animations and space visuals.
"""

import os
import json
import random
import subprocess
from datetime import datetime

# Check for required libraries
try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ Pillow not installed. Install with: pip install Pillow")

# Video settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Colors (RGB tuples for PIL)
COLORS = {
    'white': (255, 255, 255),
    'orange': (249, 115, 22),
    'blue': (59, 130, 246),
    'purple': (139, 92, 246),
    'yellow': (251, 191, 36),
    'cyan': (6, 182, 212),
}


def create_starfield_frame(width, height, num_stars=300):
    """Generate a starfield background image."""
    img = Image.new('RGB', (width, height), (5, 5, 15))
    draw = ImageDraw.Draw(img)
    
    # Add stars of varying sizes and brightness
    random.seed(42)  # Consistent starfield
    for _ in range(num_stars):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        brightness = random.randint(150, 255)
        size = random.choice([1, 1, 1, 2, 2, 3])
        
        r = brightness
        g = brightness
        b = min(255, brightness + random.randint(0, 30))
        
        if size == 1:
            draw.point((x, y), fill=(r, g, b))
        else:
            draw.ellipse([x - size, y - size, x + size, y + size], fill=(r, g, b))
    
    # Add a few bright glow stars
    for _ in range(15):
        x = random.randint(20, width - 20)
        y = random.randint(20, height - 20)
        
        for radius in range(6, 0, -1):
            alpha_factor = 1 - radius / 6
            intensity = int(150 + 105 * alpha_factor)
            color = (intensity, intensity, min(255, intensity + 30))
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
    
    return img


def get_font(size):
    """Get a font, falling back to default if custom fonts unavailable."""
    try:
        # Try common system fonts
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "arial.ttf",
            "Arial.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        
        # Fallback to default
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def get_text_size_value(text_size):
    """Get font size based on text_size parameter."""
    sizes = {
        'large': 80,
        'medium': 60,
        'small': 48
    }
    return sizes.get(text_size, 60)


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def create_scene_frame(scene, background):
    """Create a single frame for a scene with text overlay."""
    img = background.copy()
    draw = ImageDraw.Draw(img)
    
    text = scene['text']
    text_size = scene.get('text_size', 'medium')
    text_position = scene.get('text_position', 'center')
    
    font_size = get_text_size_value(text_size)
    font = get_font(font_size)
    
    # Wrap text
    max_width = VIDEO_WIDTH - 100
    lines = wrap_text(text, font, max_width, draw)
    
    # Calculate total text height
    line_height = font_size + 10
    total_height = len(lines) * line_height
    
    # Determine Y position
    if text_position == 'top':
        start_y = 200
    elif text_position == 'bottom':
        start_y = VIDEO_HEIGHT - 300 - total_height
    else:  # center
        start_y = (VIDEO_HEIGHT - total_height) // 2
    
    # Draw each line with shadow for better visibility
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        y = start_y + i * line_height
        
        # Draw shadow
        shadow_offset = 3
        draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=(0, 0, 0))
        
        # Draw main text
        draw.text((x, y), line, font=font, fill=COLORS['white'])
    
    return img


def create_video_ffmpeg(frames_data, output_path, fps=30):
    """Create video from frames using ffmpeg directly."""
    
    # Create temporary directory for frames
    temp_dir = "temp_frames"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    frame_count = 0
    
    print("🖼️ Generating frames...")
    
    for scene_idx, (scene, duration) in enumerate(frames_data):
        # Create background once per scene
        background = create_starfield_frame(VIDEO_WIDTH, VIDEO_HEIGHT)
        frame = create_scene_frame(scene, background)
        
        # Calculate number of frames for this scene
        num_frames = int(duration * fps)
        
        print(f"  📍 Scene {scene_idx + 1}: {num_frames} frames ({duration}s)")
        
        # Save frames for this scene
        for i in range(num_frames):
            frame_path = os.path.join(temp_dir, f"frame_{frame_count:05d}.png")
            frame.save(frame_path)
            frame_count += 1
    
    print(f"✅ Generated {frame_count} total frames")
    print("🎬 Encoding video with ffmpeg...")
    
    # Use ffmpeg to create video
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-framerate', str(fps),
        '-i', os.path.join(temp_dir, 'frame_%05d.png'),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'medium',
        '-crf', '23',
        output_path
    ]
    
    try:
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ FFmpeg failed: {e}")
        return None
    
    # Clean up temp frames
    print("🧹 Cleaning up temporary files...")
    for f in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, f))
    os.rmdir(temp_dir)
    
    print(f"✅ Video saved: {output_path}")
    return output_path


def render_video(script_data, output_path):
    """Render the complete video from script data."""
    
    if not PIL_AVAILABLE:
        print("❌ Pillow is required")
        return None
    
    script = script_data['script']
    scenes = script['scenes']
    
    print(f"🎬 Preparing {len(scenes)} scenes...")
    
    # Prepare frame data: (scene, duration) pairs
    frames_data = []
    for scene in scenes:
        duration = scene.get('duration', 4)
        frames_data.append((scene, duration))
    
    # Create video
    result = create_video_ffmpeg(frames_data, output_path, FPS)
    
    return result


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
    
    if not PIL_AVAILABLE:
        print("❌ Pillow is required. Install with:")
        print("   pip install Pillow")
        exit(1)
    
    # Check for ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        if result.returncode != 0:
            raise Exception("ffmpeg not working")
        print("✅ FFmpeg found")
    except Exception:
        print("❌ FFmpeg is required but not found")
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
    safe_topic = topic.lower().replace(' ', '_').replace("'", "")[:30]
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
