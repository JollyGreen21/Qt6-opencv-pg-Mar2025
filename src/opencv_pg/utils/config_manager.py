import os
import configparser
import logging
import platform
import subprocess

log = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration using a properties file"""
    
    def __init__(self, config_path=None):
        """Initialize the configuration manager with a path to the config file
        
        Args:
            config_path (str, optional): Path to the config file. Defaults to None,
                which will use the default location (project_root/config.ini).
        """
        if config_path is None:
            # Default location: project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, 'config.ini')
        
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        # Load config or create default if it doesn't exist
        if os.path.exists(config_path):
            self.load()
        else:
            self.create_default()
            self.save()
            
    def load(self):
        """Load configuration from file"""
        try:
            self.config.read(self.config_path)
            log.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            log.error(f"Error loading configuration: {e}")
            self.create_default()
            
    def save(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                self.config.write(f)
            log.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            log.error(f"Error saving configuration: {e}")
            
    def create_default(self):
        """Create default configuration"""
        # Window section
        self.config['Window'] = {
            'main_window_size_factor': '0.5',
            'doc_window_width': '800',
            'doc_window_height': '600',
            'playground_splitter_ratio': '0.75',
            'window_title': 'OpenCV Playground',
            'show_side_widget': 'false'
        }
        
        # ImageViewer section
        self.config['ImageViewer'] = {
            'base_zoom_factor': '0.002',
            'valid_extensions': '.png,.jpg,.jpeg,.bmp,.tif,.tiff'
        }
        
        # UI section
        self.config['UI'] = {
            'show_docs': 'true',
            'show_info_widgets': 'true',
            'repaint_timer_interval': '1000',  # milliseconds
            'welcome_message': 'Welcome to OpenCV Playground'
        }
        
        # Paths section
        self.config['Paths'] = {
            # Remove default_image_path
        }
        
        # Application section
        self.config['Application'] = {
            'enable_touch_events': 'false',
            'enable_high_dpi_scaling': 'true',
            'default_log_level': 'INFO',
            'log_format': '%%(levelname)s:%%(name)s:%%(lineno)d:%%(message)s',
            'block_touch_begin': 'true',
            'block_touch_end': 'true',
            'block_touch_update': 'true'
        }
        
        # DocViewer section
        self.config['DocViewer'] = {
            'template_reload_on_context_menu': 'true'
        }
        
        # Sliders section
        self.config['Sliders'] = {
            'float_scale_factor': '1000.0',
            'default_interval': '1',
            'editable_label_width': '80',
            'editable_label_height': '20',
            'decimal_places': '2',
            'tooltip_duration': '3000',
            'tooltip_y_offset': '-40',
            'show_editable_value': 'true',
            'slider_pair_value_width': '80',
            'spinbox_min_width': '70',
            'spinbox_alignment': 'center'
        }
        
        # Pipeline section
        self.config['Pipeline'] = {
            'split_percentage': '1',
            'window_width': '400',
            'window_height': '600',
            'window_offset': '30'
        }
        
        # Theme section
        self.config['Theme'] = {
            'color_scheme': 'system',  # system, light, dark
            'accent_color': '#0078d7',
            'font_family': 'Segoe UI',
            'font_size': '10',
            'custom_stylesheets_enabled': 'false',
            'custom_stylesheet_path': ''
        }
        
        # Performance section
        self.config['Performance'] = {
            'image_cache_size': '50',  # MB
            'processing_threads': '4',
            'enable_hardware_acceleration': 'true',
            'downscale_large_images': 'true',
            'max_image_dimension': '4000'  # pixels
        }
        
        # Export section
        self.config['Export'] = {
            'default_image_format': 'png',
            'jpeg_quality': '90',
            'png_compression': '9',
            'preserve_exif': 'true',
            'default_export_path': ''
        }
        
        # Shortcuts section
        self.config['Shortcuts'] = {
            'open_file': 'Ctrl+O',
            'save_file': 'Ctrl+S',
            'undo': 'Ctrl+Z',
            'redo': 'Ctrl+Y',
            'zoom_in': 'Ctrl++',
            'zoom_out': 'Ctrl+-',
            'reset_zoom': 'Ctrl+0',
            'toggle_side_panel': 'F9'
        }
        
        # RecentFiles section
        self.config['RecentFiles'] = {
            'max_recent_files': '10',
            'remember_last_opened': 'true'
        }
        
        # Language section
        self.config['Language'] = {
            'language': 'en',
            'date_format': 'MM/dd/yyyy',
            'time_format': 'HH:mm:ss'
        }
            
    def get(self, section, option, default=None, value_type=str):
        """Get a configuration value with type conversion
        
        Args:
            section (str): Configuration section
            option (str): Option name
            default: Default value if option doesn't exist
            value_type: Type to convert the value to (str, int, float, bool)
            
        Returns:
            The configuration value converted to the specified type
        """
        try:
            if not self.config.has_section(section) or not self.config.has_option(section, option):
                return default
                
            value = self.config.get(section, option)
            
            if value_type == bool:
                return value.lower() in ('true', 'yes', '1', 'on')
            elif value_type == int:
                return self.config.getint(section, option)
            elif value_type == float:
                return self.config.getfloat(section, option)
            else:
                return value
        except Exception as e:
            log.error(f"Error getting config value {section}.{option}: {e}")
            return default
            
    def set(self, section, option, value):
        """Set a configuration value
        
        Args:
            section (str): Configuration section
            option (str): Option name
            value: Value to set (will be converted to string)
        """
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
                
            self.config.set(section, option, str(value))
        except Exception as e:
            log.error(f"Error setting config value {section}.{option}: {e}")
    
    def open_config_file(self):
        """Open the configuration file in the default text editor
        
        Returns:
            bool: True if the file was opened successfully, False otherwise
        """
        try:
            if platform.system() == 'Windows':
                os.startfile(self.config_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', self.config_path))
            else:  # Linux
                subprocess.call(('xdg-open', self.config_path))
            log.info(f"Opened configuration file: {self.config_path}")
            return True
        except Exception as e:
            log.error(f"Error opening configuration file: {e}")
            return False
    
    def is_valid_image(self, file_path):
        """Check if the file is a valid image
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            bool: True if the file is a valid image, False otherwise
        """
        valid_extensions = self.get_valid_image_extensions()
        return os.path.isfile(file_path) and file_path.lower().endswith(valid_extensions)
    
    def get_default_image_dir(self):
        """Get the default directory for opening images
        
        Returns:
            str: Path to the default directory for opening images
        """
        return ''
    
    def set_default_image_dir(self, directory):
        """Save the last used directory for opening images
        
        Args:
            directory (str): Path to the directory
        """
        pass
    
    def get_valid_image_extensions(self):
        """Get the list of valid image file extensions
        
        Returns:
            tuple: A tuple of valid image file extensions
        """
        extensions_str = self.get('ImageViewer', 'valid_extensions', 
                                 '.png,.jpg,.jpeg,.bmp,.tif,.tiff')
        return tuple(extensions_str.split(','))
    
    def get_timer_interval(self, default=1000):
        """Get the repaint timer interval
        
        Args:
            default (int): Default interval if not specified in config
            
        Returns:
            int: The timer interval in milliseconds
        """
        return self.get('UI', 'repaint_timer_interval', default, int)
    
    def is_touch_events_enabled(self):
        """Check if touch events should be enabled
        
        Returns:
            bool: True if touch events should be enabled
        """
        return self.get('Application', 'enable_touch_events', False, bool)
    
    def is_high_dpi_scaling_enabled(self):
        """Check if high DPI scaling should be enabled
        
        Returns:
            bool: True if high DPI scaling should be enabled
        """
        return self.get('Application', 'enable_high_dpi_scaling', True, bool)
    
    def get_default_log_level(self):
        """Get the default logging level
        
        Returns:
            str: The default logging level (INFO, DEBUG, etc.)
        """
        return self.get('Application', 'default_log_level', 'INFO')
    
    def should_reload_template_on_context_menu(self):
        """Check if templates should be reloaded on context menu
        
        Returns:
            bool: True if templates should be reloaded
        """
        return self.get('DocViewer', 'template_reload_on_context_menu', True, bool)
        
    # New methods for slider settings
    def get_float_scale_factor(self):
        """Get the scale factor for float sliders
        
        Returns:
            float: The scale factor for float sliders
        """
        return self.get('Sliders', 'float_scale_factor', 1000.0, float)

    def get_default_interval(self):
        """Get the default interval (step size) for sliders
        
        Returns:
            int: The default interval for sliders
        """
        return self.get('Sliders', 'default_interval', 1, int)

    def get_editable_label_width(self):
        """Get the width for editable labels
        
        Returns:
            int: The width for editable labels
        """
        return self.get('Sliders', 'editable_label_width', 80, int)

    def get_editable_label_height(self):
        """Get the height for editable labels
        
        Returns:
            int: The height for editable labels
        """
        return self.get('Sliders', 'editable_label_height', 20, int)

    def get_decimal_places(self):
        """Get the number of decimal places for float values
        
        Returns:
            int: The number of decimal places for float values
        """
        return self.get('Sliders', 'decimal_places', 2, int)

    def get_tooltip_duration(self):
        """Get the duration for tooltips
        
        Returns:
            int: The duration for tooltips in milliseconds
        """
        return self.get('Sliders', 'tooltip_duration', 3000, int)

    def get_tooltip_y_offset(self):
        """Get the y offset for tooltips
        
        Returns:
            int: The y offset for tooltips in pixels
        """
        return self.get('Sliders', 'tooltip_y_offset', -40, int)
        
    def should_show_editable_value(self):
        """Check if editable value should be shown by default
        
        Returns:
            bool: True if editable value should be shown
        """
        return self.get('Sliders', 'show_editable_value', True, bool)
    
    def get_slider_pair_value_width(self):
        """Get the width for slider pair value labels
        
        Returns:
            int: The width for slider pair value labels
        """
        return self.get('Sliders', 'slider_pair_value_width', 80, int)
    
    def get_spinbox_min_width(self):
        """Get the minimum width for spinboxes
        
        Returns:
            int: The minimum width for spinboxes
        """
        return self.get('Sliders', 'spinbox_min_width', 70, int)
    
    def get_spinbox_alignment(self):
        """Get the alignment for spinboxes
        
        Returns:
            Qt.Alignment: The alignment for spinboxes
        """
        alignment_str = self.get('Sliders', 'spinbox_alignment', 'center')
        from PySide6.QtCore import Qt
        
        alignments = {
            'left': Qt.AlignLeft,
            'right': Qt.AlignRight,
            'center': Qt.AlignCenter
        }
        
        return alignments.get(alignment_str.lower(), Qt.AlignCenter)
        
    # New methods for pipeline settings
    def get_pipeline_split_percentage(self):
        """Get the default split percentage for pipeline windows
        
        Returns:
            int: The default split percentage
        """
        return self.get('Pipeline', 'split_percentage', 1, int)
        
    def get_pipeline_window_size(self):
        """Get the default window size for pipeline windows
        
        Returns:
            tuple: (width, height) tuple for window size
        """
        width = self.get('Pipeline', 'window_width', 400, int)
        height = self.get('Pipeline', 'window_height', 600, int)
        return (width, height)
        
    def get_pipeline_window_offset(self):
        """Get the default offset for staggering pipeline windows
        
        Returns:
            int: The default window offset in pixels
        """
        return self.get('Pipeline', 'window_offset', 30, int)
    
    def get_log_format(self):
        """Get the log format string
        
        Returns:
            str: The log format string
        """
        return self.get('Application', 'log_format', '%%(levelname)s:%%(name)s:%%(lineno)d:%%(message)s')
    
    # New methods for window settings
    def get_window_title(self):
        """Get the window title
        
        Returns:
            str: The window title
        """
        return self.get('Window', 'window_title', 'OpenCV Playground')
    
    def should_show_side_widget(self):
        """Check if side widget should be shown
        
        Returns:
            bool: True if side widget should be shown
        """
        return self.get('Window', 'show_side_widget', False, bool)
    
    def get_welcome_message(self):
        """Get the welcome message for the status bar
        
        Returns:
            str: The welcome message
        """
        return self.get('UI', 'welcome_message', 'Welcome to OpenCV Playground')
    
    def should_block_touch_begin(self):
        """Check if touch begin events should be blocked
        
        Returns:
            bool: True if touch begin events should be blocked
        """
        return self.get('Application', 'block_touch_begin', True, bool)
    
    def should_block_touch_end(self):
        """Check if touch end events should be blocked
        
        Returns:
            bool: True if touch end events should be blocked
        """
        return self.get('Application', 'block_touch_end', True, bool)
    
    def should_block_touch_update(self):
        """Check if touch update events should be blocked
        
        Returns:
            bool: True if touch update events should be blocked
        """
        return self.get('Application', 'block_touch_update', True, bool)
    
    # Theme methods
    def get_color_scheme(self):
        """Get the application color scheme
        
        Returns:
            str: The color scheme (system, light, dark)
        """
        return self.get('Theme', 'color_scheme', 'system')
    
    def get_accent_color(self):
        """Get the accent color
        
        Returns:
            str: The accent color as hex
        """
        return self.get('Theme', 'accent_color', '#0078d7')
    
    def get_font_settings(self):
        """Get the font settings
        
        Returns:
            tuple: (font_family, font_size)
        """
        family = self.get('Theme', 'font_family', 'Segoe UI')
        size = self.get('Theme', 'font_size', 10, int)
        return (family, size)
    
    def are_custom_stylesheets_enabled(self):
        """Check if custom stylesheets are enabled
        
        Returns:
            bool: True if custom stylesheets are enabled
        """
        return self.get('Theme', 'custom_stylesheets_enabled', False, bool)
    
    def get_custom_stylesheet_path(self):
        """Get the path to the custom stylesheet
        
        Returns:
            str: Path to the custom stylesheet
        """
        return self.get('Theme', 'custom_stylesheet_path', '')
    
    # Performance methods
    def get_image_cache_size(self):
        """Get the image cache size in MB
        
        Returns:
            int: The image cache size in MB
        """
        return self.get('Performance', 'image_cache_size', 50, int)
    
    def get_processing_threads(self):
        """Get the number of processing threads
        
        Returns:
            int: The number of processing threads
        """
        return self.get('Performance', 'processing_threads', 4, int)
    
    def is_hardware_acceleration_enabled(self):
        """Check if hardware acceleration is enabled
        
        Returns:
            bool: True if hardware acceleration is enabled
        """
        return self.get('Performance', 'enable_hardware_acceleration', True, bool)
    
    def should_downscale_large_images(self):
        """Check if large images should be downscaled
        
        Returns:
            bool: True if large images should be downscaled
        """
        return self.get('Performance', 'downscale_large_images', True, bool)
    
    def get_max_image_dimension(self):
        """Get the maximum image dimension
        
        Returns:
            int: The maximum image dimension in pixels
        """
        return self.get('Performance', 'max_image_dimension', 4000, int)
    
    # Export methods
    def get_default_image_format(self):
        """Get the default image format for saving
        
        Returns:
            str: The default image format
        """
        return self.get('Export', 'default_image_format', 'png')
    
    def get_jpeg_quality(self):
        """Get the JPEG quality setting
        
        Returns:
            int: The JPEG quality (0-100)
        """
        return self.get('Export', 'jpeg_quality', 90, int)
    
    def get_png_compression(self):
        """Get the PNG compression level
        
        Returns:
            int: The PNG compression level (0-9)
        """
        return self.get('Export', 'png_compression', 9, int)
    
    def should_preserve_exif(self):
        """Check if EXIF data should be preserved
        
        Returns:
            bool: True if EXIF data should be preserved
        """
        return self.get('Export', 'preserve_exif', True, bool)
    
    def get_default_export_path(self):
        """Get the default export path
        
        Returns:
            str: The default export path
        """
        return self.get('Export', 'default_export_path', '')
    
    # Shortcuts methods
    def get_shortcut(self, action):
        """Get the shortcut for an action
        
        Args:
            action (str): The action name
            
        Returns:
            str: The shortcut key sequence
        """
        defaults = {
            'open_file': 'Ctrl+O',
            'save_file': 'Ctrl+S',
            'undo': 'Ctrl+Z',
            'redo': 'Ctrl+Y',
            'zoom_in': 'Ctrl++',
            'zoom_out': 'Ctrl+-',
            'reset_zoom': 'Ctrl+0',
            'toggle_side_panel': 'F9'
        }
        return self.get('Shortcuts', action, defaults.get(action, ''))
    
    # Recent files methods
    def get_max_recent_files(self):
        """Get the maximum number of recent files to track
        
        Returns:
            int: The maximum number of recent files
        """
        return self.get('RecentFiles', 'max_recent_files', 10, int)
    
    def should_remember_last_opened(self):
        """Check if the last opened file should be remembered
        
        Returns:
            bool: True if the last opened file should be remembered
        """
        return self.get('RecentFiles', 'remember_last_opened', True, bool)
    
    # Language methods
    def get_language(self):
        """Get the interface language
        
        Returns:
            str: The interface language code
        """
        return self.get('Language', 'language', 'en')
    
    def get_date_format(self):
        """Get the date format
        
        Returns:
            str: The date format string
        """
        return self.get('Language', 'date_format', 'MM/dd/yyyy')
    
    def get_time_format(self):
        """Get the time format
        
        Returns:
            str: The time format string
        """
        return self.get('Language', 'time_format', 'HH:mm:ss')

# Create a singleton instance
config = ConfigManager()
