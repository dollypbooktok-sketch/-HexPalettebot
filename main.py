import os
import sys
import logging
import random
import re
from typing import Tuple, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("❌ TELEGRAM_TOKEN environment variable not set!")
    sys.exit(1)

# ============================================================================
# COLOR UTILITY FUNCTIONS
# ============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hexadecimal color to RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., "#FF5733" or "FF5733")
    
    Returns:
        Tuple of (red, green, blue) values (0-255)
    """
    hex_color = hex_color.lstrip('#')
    
    # Handle 3-digit hex (e.g., #F53 -> #FF5533)
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hexadecimal color.
    
    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
    
    Returns:
        Hex color string (e.g., "#FF5733")
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_random_color() -> str:
    """Generate a random hex color."""
    return rgb_to_hex(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )


def get_complementary_color(hex_color: str) -> str:
    """
    Calculate the complementary color (opposite on color wheel).
    
    Args:
        hex_color: Hex color string
    
    Returns:
        Complementary hex color
    """
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(255 - r, 255 - g, 255 - b)


def get_analogous_colors(hex_color: str, count: int = 2) -> list:
    """
    Generate analogous colors (colors next to each other on color wheel).
    
    Args:
        hex_color: Base hex color
        count: Number of analogous colors to generate
    
    Returns:
        List of analogous hex colors
    """
    r, g, b = hex_to_rgb(hex_color)
    colors = []
    
    for i in range(1, count + 1):
        # Shift each channel by a step
        step = 30 * i
        new_r = min(255, max(0, r + step))
        new_g = min(255, max(0, g + step))
        new_b = min(255, max(0, b + step))
        colors.append(rgb_to_hex(new_r, new_g, new_b))
    
    return colors


def get_triadic_colors(hex_color: str) -> list:
    """
    Generate triadic colors (120 degrees apart on color wheel).
    
    Args:
        hex_color: Base hex color
    
    Returns:
        List of triadic hex colors
    """
    r, g, b = hex_to_rgb(hex_color)
    colors = []
    
    # Simple triadic approximation
    for shift in [0, 120, 240]:
        # Convert to HSL-like rotation (simplified)
        new_r = min(255, max(0, (r + int(shift * 0.5)) % 256))
        new_g = min(255, max(0, (g + int(shift * 0.3)) % 256))
        new_b = min(255, max(0, (b + int(shift * 0.7)) % 256))
        colors.append(rgb_to_hex(new_r, new_g, new_b))
    
    return colors


def is_valid_hex(hex_color: str) -> bool:
    """
    Validate a hex color string.
    
    Args:
        hex_color: Hex color string
    
    Returns:
        True if valid, False otherwise
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) not in (3, 6):
        return False
    try:
        int(hex_color, 16)
        return True
    except ValueError:
        return False


def get_color_preview(hex_color: str) -> str:
    """Create a visual preview of a color using block characters."""
    return "█" * 15


def format_color_info(hex_color: str) -> str:
    """
    Format color information for display.
    
    Args:
        hex_color: Hex color string
    
    Returns:
        Formatted message string
    """
    r, g, b = hex_to_rgb(hex_color)
    comp = get_complementary_color(hex_color)
    analogous = get_analogous_colors(hex_color, 2)
    triadic = get_triadic_colors(hex_color)
    
    return (
        f"🎨 **Color Analysis**\n\n"
        f"📝 Hex: `{hex_color}`\n"
        f"🔴 RGB: ({r}, {g}, {b})\n"
        f"🔄 Complementary: `{comp}`\n"
        f"🎨 Analogous: `{analogous[0]}`, `{analogous[1]}`\n"
        f"🔺 Triadic: `{triadic[0]}`, `{triadic[1]}`, `{triadic[2]}`\n\n"
        f"Preview:\n"
        f"`{get_color_preview(hex_color)}`"
    )


def format_random_color() -> str:
    """Generate and format a random color."""
    color = generate_random_color()
    r, g, b = hex_to_rgb(color)
    comp = get_complementary_color(color)
    analogous = get_analogous_colors(color, 2)
    
    return (
        f"🎲 **Random Color Generated!**\n\n"
        f"🎨 Hex: `{color}`\n"
        f"🔴 RGB: ({r}, {g}, {b})\n"
        f"🔄 Complementary: `{comp}`\n"
        f"🎨 Analogous: `{analogous[0]}`, `{analogous[1]}`\n\n"
        f"Preview:\n"
        f"`{get_color_preview(color)}`"
    ), color


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    
    welcome = (
        f"🎨 **Welcome to HexPaletteBot, {user.first_name}!**\n\n"
        "I'm your color exploration assistant. Here's what I can do:\n\n"
        "🎲 Generate random colors\n"
        "🔄 Find complementary colors\n"
        "🎨 Create color palettes\n"
        "🔴 Convert hex to RGB and vice versa\n"
        "📊 Analyze any color\n\n"
        "💡 **Quick Start:**\n"
        "• Send any hex color like `#FF5733`\n"
        "• Send RGB like `255,87,51`\n"
        "• Use `/random` for a surprise color\n"
        "• Use `/help` for all commands"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎲 Random", callback_data="random"),
            InlineKeyboardButton("🎨 Palette", callback_data="palette"),
        ],
        [
            InlineKeyboardButton("🔄 Complementary", callback_data="complementary"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_text = (
        "📖 **HexPaletteBot Commands**\n\n"
        "**Main Commands:**\n"
        "• `/start` - Show main menu\n"
        "• `/help` - Show this help\n"
        "• `/random` - Generate random color\n"
        "• `/complementary [color]` - Find complementary\n"
        "• `/analogous [color] [count]` - Get analogous colors\n"
        "• `/convert [color]` - Convert hex to RGB\n\n"
        "**Quick Input:**\n"
        "• Send `#FF5733` - Analyze a hex color\n"
        "• Send `255,87,51` - Convert RGB to hex\n\n"
        "**Examples:**\n"
        "• `/random`\n"
        "• `/complementary #FF5733`\n"
        "• `/analogous #FF5733 3`\n"
        "• `/convert #FF5733`\n\n"
        "💡 Both 3-digit and 6-digit hex supported!"
    )
    await update.message.reply_text(help_text)


async def random_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /random command."""
    message, color = format_random_color()
    
    keyboard = [
        [
            InlineKeyboardButton("🎲 Another", callback_data="random"),
            InlineKeyboardButton("🔄 Complement", callback_data=f"comp_{color}"),
        ],
        [
            InlineKeyboardButton("🎨 Palette", callback_data=f"palette_{color}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)


async def complementary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /complementary command."""
    args = context.args
    
    # Check if we have a color from context
    if not args and context.user_data.get('last_color'):
        color = context.user_data['last_color']
    elif args:
        color = args[0]
    else:
        await update.message.reply_text(
            "🔄 Please provide a hex color!\n"
            "Example: `/complementary #FF5733`\n\n"
            "Or send me a color first, then use this command."
        )
        return
    
    if not is_valid_hex(color):
        await update.message.reply_text(
            "❌ Invalid hex color!\n"
            "Use format like `#FF5733` or `#F53`"
        )
        return
    
    comp = get_complementary_color(color)
    r, g, b = hex_to_rgb(comp)
    
    await update.message.reply_text(
        f"🔄 **Complementary Color**\n\n"
        f"Original: `{color}`\n"
        f"Complementary: `{comp}`\n"
        f"RGB: ({r}, {g}, {b})\n\n"
        f"Preview:\n"
        f"`{get_color_preview(comp)}`"
    )


async def analogous(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /analogous command."""
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "🎨 Please provide a hex color!\n"
            "Example: `/analogous #FF5733`\n"
            "With count: `/analogous #FF5733 3`"
        )
        return
    
    color = args[0]
    count = int(args[1]) if len(args) > 1 else 2
    
    if not is_valid_hex(color):
        await update.message.reply_text(
            "❌ Invalid hex color!\n"
            "Use format like `#FF5733` or `#F53`"
        )
        return
    
    colors = get_analogous_colors(color, count)
    
    message = f"🎨 **Analogous Colors**\n\nOriginal: `{color}`\n\n"
    for i, c in enumerate(colors, 1):
        r, g, b = hex_to_rgb(c)
        message += f"Color {i}: `{c}` - RGB({r}, {g}, {b})\n"
    
    await update.message.reply_text(message)


async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /convert command."""
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "🔄 Please provide a color!\n"
            "Example: `/convert #FF5733`\n"
            "Or: `/convert 255,87,51`"
        )
        return
    
    input_text = args[0]
    
    # Try hex conversion
    if input_text.startswith('#'):
        if is_valid_hex(input_text):
            r, g, b = hex_to_rgb(input_text)
            await update.message.reply_text(
                f"🔄 **Color Conversion**\n\n"
                f"Hex: `{input_text}`\n"
                f"RGB: ({r}, {g}, {b})\n\n"
                f"Preview:\n"
                f"`{get_color_preview(input_text)}`"
            )
        else:
            await update.message.reply_text("❌ Invalid hex color!")
        return
    
    # Try RGB conversion
    if ',' in input_text:
        try:
            parts = [x.strip() for x in input_text.split(',')]
            if len(parts) == 3:
                r, g, b = map(int, parts)
                if all(0 <= x <= 255 for x in (r, g, b)):
                    hex_color = rgb_to_hex(r, g, b)
                    await update.message.reply_text(
                        f"🔄 **Color Conversion**\n\n"
                        f"RGB: ({r}, {g}, {b})\n"
                        f"Hex: `{hex_color}`\n\n"
                        f"Preview:\n"
                        f"`{get_color_preview(hex_color)}`"
                    )
                else:
                    await update.message.reply_text("❌ RGB values must be between 0 and 255!")
            else:
                await update.message.reply_text("❌ Use format: 255, 87, 51")
        except Exception:
            await update.message.reply_text("❌ Invalid format! Use: 255, 87, 51")
        return
    
    await update.message.reply_text(
        "❌ Invalid input!\n"
        "Use hex like `#FF5733` or RGB like `255,87,51`"
    )


# ============================================================================
# MESSAGE HANDLER
# ============================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any non-command messages."""
    text = update.message.text.strip()
    context.user_data['last_text'] = text
    
    # Check if hex color
    if text.startswith('#'):
        if is_valid_hex(text):
            context.user_data['last_color'] = text
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Complement", callback_data=f"comp_{text}"),
                    InlineKeyboardButton("🎨 Palette", callback_data=f"palette_{text}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                format_color_info(text),
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "❌ Invalid hex color!\n"
                "Use format like `#FF5733` or `#F53`"
            )
        return
    
    # Check if RGB
    if ',' in text:
        try:
            parts = [x.strip() for x in text.split(',')]
            if len(parts) == 3:
                r, g, b = map(int, parts)
                if all(0 <= x <= 255 for x in (r, g, b)):
                    hex_color = rgb_to_hex(r, g, b)
                    context.user_data['last_color'] = hex_color
                    
                    await update.message.reply_text(
                        f"🎨 **Color Analysis**\n\n"
                        f"RGB: ({r}, {g}, {b})\n"
                        f"Hex: `{hex_color}`\n\n"
                        f"Preview:\n"
                        f"`{get_color_preview(hex_color)}`"
                    )
                else:
                    await update.message.reply_text(
                        "❌ RGB values must be between 0 and 255!"
                    )
            else:
                await update.message.reply_text(
                    "❌ Use format: 255, 87, 51"
                )
        except Exception:
            await update.message.reply_text(
                "❌ Invalid format!\n"
                "Use: 255, 87, 51"
            )
        return
    
    # Unknown message
    await update.message.reply_text(
        f"📝 I received: `{text}`\n\n"
        "Send me a hex color like `#FF5733` or RGB like `255,87,51`\n"
        "Use `/help` for all commands!"
    )


# ============================================================================
# CALLBACK HANDLER
# ============================================================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_data = context.user_data
    
    # Random color
    if data == "random":
        message, color = format_random_color()
        
        keyboard = [
            [
                InlineKeyboardButton("🎲 Another", callback_data="random"),
                InlineKeyboardButton("🔄 Complement", callback_data=f"comp_{color}"),
            ],
            [
                InlineKeyboardButton("🎨 Palette", callback_data=f"palette_{color}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    # Help
    elif data == "help":
        await query.edit_message_text(
            "📖 **HexPaletteBot Commands**\n\n"
            "• `/start` - Main menu\n"
            "• `/help` - This help\n"
            "• `/random` - Random color\n"
            "• `/complementary #FF5733` - Complementary\n"
            "• `/analogous #FF5733 3` - Analogous\n"
            "• `/convert #FF5733` - Convert\n\n"
            "Send `#FF5733` or `255,87,51` for quick analysis!"
        )
    
    # Complementary from button
    elif data == "complementary":
        # Use last color or generate random
        color = user_data.get('last_color') or generate_random_color()
        comp = get_complementary_color(color)
        r, g, b = hex_to_rgb(comp)
        
        keyboard = [
            [InlineKeyboardButton("🎨 Back", callback_data=f"back_{color}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🔄 **Complementary Color**\n\n"
            f"Original: `{color}`\n"
            f"Complementary: `{comp}`\n"
            f"RGB: ({r}, {g}, {b})\n\n"
            f"Preview:\n"
            f"`{get_color_preview(comp)}`",
            reply_markup=reply_markup
        )
    
    # Palette from button
    elif data == "palette":
        color = generate_random_color()
        r, g, b = hex_to_rgb(color)
        comp = get_complementary_color(color)
        analogous = get_analogous_colors(color, 2)
        triadic = get_triadic_colors(color)
        
        message = (
            f"🎨 **Color Palette**\n\n"
            f"Main: `{color}` - RGB({r}, {g}, {b})\n"
            f"Complementary: `{comp}`\n"
            f"Analogous: `{analogous[0]}`, `{analogous[1]}`\n"
            f"Triadic: `{triadic[0]}`, `{triadic[1]}`, `{triadic[2]}`\n\n"
            f"Preview:\n"
            f"`{get_color_preview(color)}`"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎲 New Palette", callback_data="palette")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    # Handle color-specific callbacks
    elif data.startswith("comp_"):
        color = data.split("_")[1]
        comp = get_complementary_color(color)
        r, g, b = hex_to_rgb(comp)
        
        keyboard = [
            [InlineKeyboardButton("🎨 Back", callback_data=f"back_{color}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🔄 **Complementary Color**\n\n"
            f"Original: `{color}`\n"
            f"Complementary: `{comp}`\n"
            f"RGB: ({r}, {g}, {b})\n\n"
            f"Preview:\n"
            f"`{get_color_preview(comp)}`",
            reply_markup=reply_markup
        )
    
    elif data.startswith("palette_"):
        color = data.split("_")[1]
        r, g, b = hex_to_rgb(color)
        comp = get_complementary_color(color)
        analogous = get_analogous_colors(color, 2)
        triadic = get_triadic_colors(color)
        
        message = (
            f"🎨 **Color Palette**\n\n"
            f"Main: `{color}` - RGB({r}, {g}, {b})\n"
            f"Complementary: `{comp}`\n"
            f"Analogous: `{analogous[0]}`, `{analogous[1]}`\n"
            f"Triadic: `{triadic[0]}`, `{triadic[1]}`, `{triadic[2]}`\n\n"
            f"Preview:\n"
            f"`{get_color_preview(color)}`"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Back", callback_data=f"back_{color}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif data.startswith("back_"):
        color = data.split("_")[1]
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Complement", callback_data=f"comp_{color}"),
                InlineKeyboardButton("🎨 Palette", callback_data=f"palette_{color}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            format_color_info(color),
            reply_markup=reply_markup
        )
    
    else:
        await query.edit_message_text("❌ Unknown command. Please try again.")


# ============================================================================
# ERROR HANDLER
# ============================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
        except Exception:
            pass


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main() -> None:
    """Start the bot."""
    try:
        logger.info("🚀 Starting HexPaletteBot...")
        logger.info(f"🤖 Bot Token: {TOKEN[:10]}... (truncated)")
        
        # Create application
        app = Application.builder().token(TOKEN).build()
        
        # Add command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("random", random_color))
        app.add_handler(CommandHandler("complementary", complementary))
        app.add_handler(CommandHandler("analogous", analogous))
        app.add_handler(CommandHandler("convert", convert))
        
        # Add message handler for non-commands
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add callback handler for buttons
        app.add_handler(CallbackQueryHandler(button_callback))
        
        # Add error handler
        app.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("✅ Bot is running and ready for messages!")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
