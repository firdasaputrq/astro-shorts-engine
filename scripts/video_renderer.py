"""
Video Renderer Agent - FULL VERSION WITH AUDIO
Creates MP4 videos from formatted scripts with:
- Animated starfield backgrounds
- Planet graphics (Earth, Mars, Jupiter, Saturn, etc.)
- Multiple animation types (fade, zoom, slide, pulse)
- Text effects with shadows and outlines
- Scene transitions
- Background music (randomly selected)
"""

import os
import sys
import json
import random
import math
import subprocess
from datetime import datetime

# Import dependencies with proper error handling
try:
    import moviepy
    from moviepy.editor import (
        TextClip, CompositeVideoClip, ColorClip, 
        ImageClip, concatenate_videoclips, VideoClip,
        AudioFileClip, CompositeAudioClip
    )
    from moviepy.video.fx.all import fadein, fadeout, resize
    from moviepy.audio.fx.all import audio_fadeout, audio_fadein
    MOVIEPY_AVAILABLE = True
    print("✅ MoviePy loaded successfully")
except ImportError as e:
    print(f"❌ MoviePy import error: {e}")
    MOVIEPY_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import numpy as np
    PIL_AVAILABLE = True
    print("✅ Pillow loaded successfully")
except ImportError:
    PIL_AVAILABLE = False
    print("❌ Pillow not installed")


# =============================================================================
# VIDEO SETTINGS
# =============================================================================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Audio settings
AUDIO_DIR = "assets/audio"
MUSIC_VOLUME = 0.3  # 30% volume so it doesn't overpower text

# Color palette
COLORS = {
    'white': (255, 255, 255),
    'orange': (249, 115, 22),
    'blue': (59, 130, 246),
    'purple': (139, 92, 246),
    'yellow': (251, 191, 36),
    'cyan': (6, 182, 212),
    'red': (239, 68, 68),
    'green': (34, 197, 94),
}

COLORS_HEX = {
    'white': '#FFFFFF',
    'orange': '#F97316',
    'blue': '#3B82F6',
    'purple': '#8B5CF6',
    'yellow': '#FBBF24',
    'cyan': '#06B6D4',
}


# =============================================================================
# AUDIO FUNCTIONS
# =============================================================================
def get_available_music():
    """Find all available music files."""
    music_files = []
    
    if os.path.exists(AUDIO_DIR):
        for filename in os.listdir(AUDIO_DIR):
            if filename.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                filepath = os.path.join(AUDIO_DIR, filename)
                music_files.append(filepath)
    
    return music_files


def select_random_music():
    """Randomly select a music track."""
    music_files = get_available_music()
    
    if not music_files:
        print("⚠️ No music files found in assets/audio/")
        return None
    
    selected = random.choice(music_files)
    print(f"🎵 Selected music: {os.path.basename(selected)}")
    return selected


def add_background_music(video_clip, music_path, volume=MUSIC_VOLUME):
    """Add background music to a video clip."""
    if not music_path or not os.path.exists(music_path):
        print("⚠️ No music file available, video will be silent")
        return video_clip
    
    try:
        # Load audio
        audio = AudioFileClip(music_path)
        
        # Get video duration
        video_duration = video_clip.duration
        
        # Loop or trim audio to match video length
        if audio.duration < video_duration:
            # Loop the audio
            loops_needed = int(video_duration / audio.duration) + 1
            audio = concatenate_audioclips([audio] * loops_needed)
        
        # Trim to video duration
        audio = audio.subclip(0, video_duration)
        
        # Apply volume adjustment
        audio = audio.volumex(volume)
        
        # Add fade in and fade out
        audio = audio_fadein(audio, 0.5)
        audio = audio_fadeout(audio, 1.0)
        
        # Set audio to video
        video_with_audio = video_clip.set_audio(audio)
        
        print(f"✅ Added background music ({video_duration:.1f}s)")
        return video_with_audio
        
    except Exception as e:
        print(f"⚠️ Could not add music: {e}")
        return video_clip


def concatenate_audioclips(clips):
    """Helper to concatenate audio clips."""
    from moviepy.editor import concatenate_audioclips as concat_audio
    return concat_audio(clips)


# =============================================================================
# STARFIELD BACKGROUND GENERATOR
# =============================================================================
def create_starfield_background(width, height, num_stars=400, seed=None):
    """
    Generate a beautiful starfield background with:
    - Multiple star sizes and brightness levels
    - Glowing bright stars
    - Subtle nebula-like color gradients
    """
    if seed:
        random.seed(seed)
    
    # Create base dark space gradient
    img = Image.new('RGB', (width, height), (3, 3, 12))
    draw = ImageDraw.Draw(img)
    
    # Add subtle vertical gradient (darker at top and bottom)
    for y in range(height):
        dist = abs(y - height // 2) / (height // 2)
        darkness = int(dist * 8)
        base_color = max(0, 12 - darkness)
        for x in range(0, width, 50):
            draw.rectangle([x, y, x + 50, y + 1], fill=(3, 3, base_color))
    
    # Add nebula-like subtle color regions
    for _ in range(3):
        cx = random.randint(0, width)
        cy = random.randint(0, height)
        nebula_color = random.choice([
            (20, 10, 30),
            (10, 15, 25),
            (15, 10, 20),
        ])
        radius = random.randint(200, 400)
        for r in range(radius, 0, -20):
            alpha = 0.1 * (1 - r / radius)
            blend_color = tuple(int(c * alpha) for c in nebula_color)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=blend_color)
    
    # Layer 1: Distant small stars
    for _ in range(num_stars):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        brightness = random.randint(80, 180)
        r = brightness
        g = brightness
        b = min(255, brightness + random.randint(0, 40))
        draw.point((x, y), fill=(r, g, b))
    
    # Layer 2: Medium stars
    for _ in range(num_stars // 4):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        brightness = random.randint(150, 220)
        size = random.choice([1, 2, 2])
        color = (brightness, brightness, min(255, brightness + 20))
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
    
    # Layer 3: Bright prominent stars with glow
    for _ in range(20):
        x = random.randint(20, width - 20)
        y = random.randint(20, height - 20)
        
        for radius in range(8, 0, -1):
            intensity = int(100 + 155 * (1 - radius / 8))
            glow_color = (intensity, intensity, min(255, intensity + 30))
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=glow_color)
        
        draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(255, 255, 255))
    
    # Layer 4: Extra-bright stars with cross flare
    for _ in range(5):
        x = random.randint(50, width - 50)
        y = random.randint(50, height - 50)
        
        for dx in range(-15, 16):
            intensity = int(200 * (1 - abs(dx) / 15))
            if intensity > 0:
                draw.point((x + dx, y), fill=(intensity, intensity, intensity))
        
        for dy in range(-15, 16):
            intensity = int(200 * (1 - abs(dy) / 15))
            if intensity > 0:
                draw.point((x, y + dy), fill=(intensity, intensity, intensity))
        
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 255, 255))
    
    return np.array(img)


# =============================================================================
# PLANET GENERATOR
# =============================================================================
def create_planet(planet_type, size=200):
    """Generate planet graphics programmatically."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    radius = size // 2 - 5
    
    planet_schemes = {
        'earth': {
            'base': (30, 100, 180),
            'secondary': (34, 139, 34),
            'highlight': (255, 255, 255),
        },
        'mars': {
            'base': (193, 68, 14),
            'secondary': (139, 69, 19),
            'highlight': (210, 105, 30),
        },
        'jupiter': {
            'base': (255, 200, 150),
            'secondary': (210, 160, 120),
            'highlight': (255, 220, 180),
            'bands': True,
        },
        'saturn': {
            'base': (210, 180, 140),
            'secondary': (238, 220, 170),
            'highlight': (255, 240, 200),
            'rings': True,
        },
        'venus': {
            'base': (255, 198, 145),
            'secondary': (218, 165, 105),
            'highlight': (255, 220, 180),
        },
        'neptune': {
            'base': (70, 130, 200),
            'secondary': (100, 149, 237),
            'highlight': (135, 180, 255),
        },
        'moon': {
            'base': (180, 180, 180),
            'secondary': (140, 140, 140),
            'highlight': (220, 220, 220),
        },
        'sun': {
            'base': (255, 200, 50),
            'secondary': (255, 150, 0),
            'highlight': (255, 255, 150),
            'glow': True,
        },
    }
    
    scheme = planet_schemes.get(planet_type, planet_schemes['earth'])
    
    if scheme.get('glow'):
        for r in range(radius + 20, radius, -2):
            draw.ellipse([center - r, center - r, center + r, center + r], 
                        fill=scheme['highlight'])
    
    draw.ellipse([center - radius, center - radius, 
                  center + radius, center + radius], 
                 fill=scheme['base'])
    
    if scheme.get('bands'):
        band_colors = [scheme['base'], scheme['secondary'], scheme['highlight']]
        band_height = radius * 2 // 6
        for i in range(6):
            y_start = center - radius + i * band_height
            color = band_colors[i % len(band_colors)]
            for y in range(y_start, min(y_start + band_height, center + radius)):
                dy = abs(y - center)
                if dy < radius:
                    dx = int(math.sqrt(radius**2 - dy**2))
                    draw.line([(center - dx, y), (center + dx, y)], fill=color)
    
    random.seed(hash(planet_type))
    for _ in range(8):
        dx = random.randint(-radius // 2, radius // 2)
        dy = random.randint(-radius // 2, radius // 2)
        if dx**2 + dy**2 < (radius // 2)**2:
            spot_size = random.randint(5, 15)
            spot_color = scheme['secondary']
            draw.ellipse([center + dx - spot_size, center + dy - spot_size,
                         center + dx + spot_size, center + dy + spot_size],
                        fill=spot_color)
    
    highlight_x = center - radius // 3
    highlight_y = center - radius // 3
    for r in range(radius // 4, 0, -2):
        draw.ellipse([highlight_x - r, highlight_y - r,
                     highlight_x + r, highlight_y + r],
                    fill=scheme['highlight'])
    
    if scheme.get('rings'):
        ring_inner = int(radius * 1.3)
        ring_outer = int(radius * 1.8)
        ring_color = (200, 180, 140)
        
        for r in range(ring_inner, ring_outer, 2):
            draw.ellipse([center - r, center - 8, center + r, center + 8], 
                        outline=ring_color, width=1)
    
    return np.array(img)


# =============================================================================
# TEXT AND ANIMATION UTILITIES  
# =============================================================================
def get_fontsize(text_size):
    """Get font size based on text_size parameter."""
    sizes = {
        'large': 76,
        'medium': 58,
        'small': 46
    }
    return sizes.get(text_size, 58)


def create_animated_text_clip(text, duration, fontsize, position='center', 
                               animation='fade_in', color='white'):
    """Create a text clip with animation effects."""
    try:
        txt = TextClip(
            text,
            fontsize=fontsize,
            color=COLORS_HEX.get(color, '#FFFFFF'),
            font='DejaVu-Sans-Bold',
            size=(VIDEO_WIDTH - 80, None),
            method='caption',
            align='center',
            stroke_color='black',
            stroke_width=3
        )
        txt = txt.set_duration(duration)
        
        if position == 'top':
            y_pos = 180
        elif position == 'bottom':
            y_pos = VIDEO_HEIGHT - 400
        else:
            y_pos = 'center'
        
        if y_pos == 'center':
            txt = txt.set_position('center')
        else:
            txt = txt.set_position(('center', y_pos))
        
        if animation == 'fade_in':
            txt = txt.crossfadein(0.5)
        elif animation == 'fade_out':
            txt = txt.crossfadeout(0.5)
        elif animation in ['zoom_in', 'slide_left', 'slide_right', 'pulse']:
            txt = txt.crossfadein(0.4)
        else:
            txt = txt.crossfadein(0.3)
        
        return txt
        
    except Exception as e:
        print(f"⚠️ TextClip creation error: {e}")
        return None


# =============================================================================
# SCENE AND VIDEO CREATION
# =============================================================================
def get_planet_for_topic(topic, visual_hint=""):
    """Determine which planet to show based on topic or visual hint."""
    topic_lower = (topic + " " + visual_hint).lower()
    
    if 'earth' in topic_lower:
        return 'earth'
    elif 'mars' in topic_lower:
        return 'mars'
    elif 'jupiter' in topic_lower:
        return 'jupiter'
    elif 'saturn' in topic_lower:
        return 'saturn'
    elif 'venus' in topic_lower:
        return 'venus'
    elif 'neptune' in topic_lower or 'uranus' in topic_lower:
        return 'neptune'
    elif 'moon' in topic_lower or 'lunar' in topic_lower:
        return 'moon'
    elif 'sun' in topic_lower or 'solar' in topic_lower:
        return 'sun'
    else:
        return random.choice(['earth', 'mars', 'jupiter', 'saturn', 'neptune'])


def create_scene_with_planet(scene, bg_array, planet_type=None, show_planet=True):
    """Create a complete scene with background, planet, and text."""
    duration = scene.get('duration', 4)
    
    bg_clip = ImageClip(bg_array).set_duration(duration)
    
    layers = [bg_clip]
    
    if show_planet and planet_type:
        planet_array = create_planet(planet_type, size=250)
        planet_clip = ImageClip(planet_array, ismask=False)
        planet_clip = planet_clip.set_duration(duration)
        
        scene_num = scene.get('scene_number', 1)
        if scene_num % 3 == 1:
            planet_pos = (VIDEO_WIDTH - 300, 200)
        elif scene_num % 3 == 2:
            planet_pos = (50, VIDEO_HEIGHT - 450)
        else:
            planet_pos = (VIDEO_WIDTH - 280, VIDEO_HEIGHT - 500)
        
        planet_clip = planet_clip.set_position(planet_pos)
        planet_clip = planet_clip.crossfadein(0.5)
        
        layers.append(planet_clip)
    
    txt_clip = create_animated_text_clip(
        scene['text'],
        duration,
        get_fontsize(scene.get('text_size', 'medium')),
        scene.get('text_position', 'center'),
        scene.get('animation', 'fade_in'),
        'white'
    )
    
    if txt_clip:
        layers.append(txt_clip)
    
    return CompositeVideoClip(layers, size=(VIDEO_WIDTH, VIDEO_HEIGHT))


def create_scene_clip(scene, bg_array, idea_topic=""):
    """Create a scene clip, deciding whether to include planet."""
    visual_hint = scene.get('visual', '')
    scene_num = scene.get('scene_number', 1)
    
    show_planet = scene_num in [1, 3, 5]
    
    planet_type = None
    if show_planet:
        planet_type = get_planet_for_topic(idea_topic, visual_hint)
    
    return create_scene_with_planet(scene, bg_array, planet_type, show_planet)


def render_video(script_data, output_path):
    """Render the complete video from script data with background music."""
    
    if not MOVIEPY_AVAILABLE or not PIL_AVAILABLE:
        print("❌ Required libraries not available")
        return None
    
    idea = script_data.get('idea', {})
    script = script_data.get('script', {})
    scenes = script.get('scenes', [])
    
    if not scenes:
        print("❌ No scenes found in script")
        return None
    
    topic = idea.get('topic', 'Space')
    
    print(f"🎬 Rendering {len(scenes)} scenes...")
    print(f"📝 Topic: {topic}")
    
    # Generate starfield background
    print("🌌 Creating starfield background...")
    bg_array = create_starfield_background(VIDEO_WIDTH, VIDEO_HEIGHT, num_stars=400, seed=42)
    
    # Build scene clips
    scene_clips = []
    total_duration = 0
    
    for i, scene in enumerate(scenes):
        scene_num = scene.get('scene_number', i + 1)
        duration = scene.get('duration', 4)
        total_duration += duration
        
        print(f"  📍 Scene {scene_num} ({duration}s): {scene['text'][:45]}...")
        
        clip = create_scene_clip(scene, bg_array, topic)
        scene_clips.append(clip)
    
    print(f"⏱️ Total duration: {total_duration} seconds")
    
    # Concatenate all scenes
    print("🔗 Combining scenes...")
    final = concatenate_videoclips(scene_clips, method="compose")
    
    # Add fade in/out
    final = final.fadein(0.5).fadeout(0.5)
    
    # Add background music
    print("🎵 Adding background music...")
    music_path = select_random_music()
    if music_path:
        final = add_background_music(final, music_path)
    
    # Export video
    print(f"💾 Exporting video to {output_path}...")
    print("   (This may take 1-2 minutes)")
    
    final.write_videofile(
        output_path,
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=2,
        logger=None,
        bitrate='5000k'
    )
    
    # Cleanup
    print("🧹 Cleaning up...")
    final.close()
    for clip in scene_clips:
        clip.close()
    
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Video rendered successfully!")
        print(f"📦 File size: {file_size:.2f} MB")
        return output_path
    else:
        print("❌ Video file was not created")
        return None


# =============================================================================
# FILE MANAGEMENT
# =============================================================================
def get_ready_scripts(scripts_dir="scripts_output"):
    """Find scripts that are ready to render."""
    if not os.path.exists(scripts_dir):
        return []
    
    ready = []
    for filename in os.listdir(scripts_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(scripts_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                if data.get('status') == 'ready_to_render':
                    ready.append((filepath, data))
            except Exception as e:
                print(f"⚠️ Could not read {filename}: {e}")
    
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


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    print("=" * 60)
    print("🎥 ASTRO SHORTS ENGINE - Full Video Renderer")
    print("   Now with background music! 🎵")
    print("=" * 60)
    print()
    
    if not MOVIEPY_AVAILABLE:
        print("❌ MoviePy is required but not available")
        exit(1)
    
    if not PIL_AVAILABLE:
        print("❌ Pillow is required but not available")
        exit(1)
    
    print("✅ All dependencies loaded")
    
    # Check for music
    music_files = get_available_music()
    print(f"🎵 Found {len(music_files)} music tracks available")
    
    print()
    
    # Create output directory
    output_dir = "videos_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Find scripts ready to render
    ready_scripts = get_ready_scripts()
    print(f"📚 Found {len(ready_scripts)} scripts ready to render")
    
    if not ready_scripts:
        print("✨ No scripts waiting to render.")
        return
    
    # Render the first ready script
    filepath, script_data = ready_scripts[0]
    topic = script_data.get('idea', {}).get('topic', 'untitled')
    
    print()
    print(f"🎬 Selected for rendering: {topic}")
    print("-" * 60)
    
    # Generate output filename
    safe_topic = "".join(c if c.isalnum() or c == ' ' else '' for c in topic)
    safe_topic = safe_topic.lower().replace(' ', '_')[:30]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"{output_dir}/{safe_topic}_{timestamp}.mp4"
    
    try:
        result = render_video(script_data, output_path)
        
        if result:
            update_script_status(filepath, 'rendered', output_path)
            
            print()
            print("=" * 60)
            print("🎉 VIDEO RENDERING COMPLETE!")
            print("=" * 60)
            print(f"📹 Output: {output_path}")
            print("🚀 Next step: YouTube upload")
            print("=" * 60)
        else:
            print("❌ Rendering failed")
            exit(1)
            
    except Exception as e:
        print(f"❌ Rendering error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
