import logging
from pathlib import Path

import cv2
import numpy as np
# from cv2.typing import Point

from . import cv2_constants as cvc
from . import params
from .base_transform import BaseTransform

log = logging.getLogger(__name__)


def is_gray(img):
    """Return True if this appears to be a single channel (gray) image"""
    if len(img.shape) == 2:
        return True
    if len(img.shape) >= 3 and img.shape[2] == 1:
        return True
    return False


def make_gray(img_in):
    """Returns Gray image as in BGR2GRAY if 3 channels detected"""
    shape = img_in.shape
    if len(shape) == 3:
        return cv2.cvtColor(img_in, cv2.COLOR_BGR2GRAY)
    return img_in


def is_gray_uint8(img_in):
    """Raises TypeError if img is not gray uint8"""
    if is_gray(img_in) and img_in.dtype == np.uint8:
        return
    raise TypeError(
        "Incoming image must be np.uint8 and have 1 channel. "
        "Got dtype={}, shape={}".format(img_in.dtype, img_in.shape)
    )


class LoadImage(BaseTransform):
    def __init__(self, path: str):
        """Loads and returns an img at path

        Args:
            path (str): path to image file
        """
        super().__init__()
        if path is None or not path:
            log.error("No file path provided for image loading")
            raise ValueError("Image path cannot be None or empty")
        
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        self.img = cv2.imread(path)

    def draw(self, img, extra):
        return self.img


class DrawLinesByPointAndAngle(BaseTransform):
    """Draws infinte lines from direction and magnitude"""

    color = params.ColorPicker(default=(0, 0, 255))
    thickness = params.IntSlider(min_val=1, max_val=100, default=2)
    line_type = params.ComboBox(
        options=list(cvc.LINES.keys()), options_map=cvc.LINES, default="8-Connected"
    )
    show_points = params.CheckBox(default=True)
    mult = params.SpinBox(
        min_val=0,
        max_val=2000,
        default=1000,
        step=100,
        help_text="Multiplier for line length. Increase if lines "
        "do not extend full length of image."
    )

    def draw(self, img_in, extra_in):
        """Draws lines on img_in by a point and angle

        Args:
            img_in (np.ndarray): Image in to draw onto
            extra_in ([(rho, theta), ..]): List of rho, theta pairs, as returned
                by HoughLines

        Returns:
            np.ndarray: Updated image
        """
        img = np.copy(img_in)
        if extra_in is None:
            return img

        b, g, r = self.color
        if is_gray(img):
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img_y, img_x = img_in.shape[:2]
        for rho, theta in extra_in:
            pt1, pt2 = self._get_endpoints(rho, theta, img_x, img_y)
            cv2.line(img, pt1, pt2, (b, g, r), self.thickness, cvc.LINES[self.line_type])
        return img

    def _get_endpoints(self, rho, theta, img_x, img_y):
        """Return some endpoints for a line based on point and angle

        Kudos: https://stackoverflow.com/questions/18782873/houghlines-transform-in-opencv
        """
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho
        y0 = b * rho
        x1 = round(x0 + self.mult * (-b))
        y1 = round(y0 + self.mult * a)
        x2 = round(x0 - self.mult * (-b))
        y2 = round(y0 - self.mult * a)

        pt1 = (x1, y1)
        pt2 = (x2, y2)

        return pt1, pt2


class DrawLinesByEndpoints(BaseTransform):
    """Draws lines between points"""

    color = params.ColorPicker(default=(0, 0, 255))
    thickness = params.IntSlider(min_val=1, max_val=100, default=2)
    line_type = params.ComboBox(
        options=list(cvc.LINES.keys()), options_map=cvc.LINES, default="8-Connected"
    )

    def draw(self, img_in, extra_in):
        """Draws lines on img_in via point pairs

        Args:
            img_in (np.ndarray): Image in to draw onto
            extra_in ([(x1, y1, x2, y2), ..]): Iterable of two point pairs

        Returns:
            np.ndarray: Updated image
        """
        img = np.copy(img_in)
        if extra_in is None:
            return img

        if is_gray(img):
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        for x1, y1, x2, y2 in extra_in:
            cv2.line(img, (x1, y1), (x2, y2), self.color, self.thickness, cvc.LINES[self.line_type])
        return img


class DrawCircles(BaseTransform):
    """Draws circles"""

    color = params.ColorPicker(default=(0, 0, 255))
    thickness = params.IntSlider(min_val=1, max_val=100, default=2)
    line_type = params.ComboBox(
        options=list(cvc.LINES.keys()), options_map=cvc.LINES, default="8-Connected"
    )

    def draw(self, img_in, extra_in):
        """Draws circles onto img_in via x, y, and radius

        Args:
            img_in (np.ndarray): Incoming image to draw on
            extra_in ([(x, y, radius), ...]): Iterable of (x, y, radius) tuples

        Returns:
            np.ndarray: Updated Image
        """
        img = np.copy(img_in)
        if extra_in is None:
            return img

        if is_gray(img):
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        for x, y, radius in extra_in:
            cv2.circle(img, (x, y), radius, self.color, self.thickness, cvc.LINES[self.line_type])
        return img


class DrawCirclesFromPoints(BaseTransform):
    """Draws circles from incoming Points"""

    color = params.ColorPicker(default=(0, 0, 255))
    radius = params.IntSlider(min_val=1, max_val=50, default=2)
    thickness = params.IntSlider(min_val=-1, max_val=20, default=-1)
    line_type = params.ComboBox(
        options=list(cvc.LINES.keys()), options_map=cvc.LINES, default="8-Connected"
    )

    def draw(self, img_in, extra_in):
        """Draws circles onto img_in via x, y

        Args:
            img_in (np.ndarray): Incoming image to draw on
            extra_in ([(x, y), ...]): Iterable of (x, y) tuples

        Some tools like GetGoodFeaturesToTrack return an N x 1 x 2 array, so
        if that's found we reshape it into N x 2 first.

        Returns:
            np.ndarray: Updated Image
        """
        if extra_in is None:
            return img_in

        img = np.copy(img_in)

        if is_gray(img_in):
            img = cv2.cvtColor(img_in, cv2.COLOR_GRAY2BGR)

        points = extra_in

        if isinstance(extra_in, np.ndarray):
            points = extra_in.reshape(-1, 2)

        for x, y in points:
            cv2.circle(img, (x, y), self.radius, self.color, self.thickness, cvc.LINES[self.line_type])
        return img


class DrawCornerSubPix(BaseTransform):
    """Draws points for CornerSubPix and its original contour points"""

    good_feat_color = params.ColorPicker(default=(0, 0, 255))
    good_feat_radius = params.IntSlider(min_val=1, max_val=50, default=3)
    good_feat_thickness = params.IntSlider(min_val=-1, max_val=20, default=-1)
    good_feat_line_type = params.ComboBox(
        options=list(cvc.LINES.keys()), options_map=cvc.LINES, default="8-Connected"
    )
    corners_color = params.ColorPicker(default=(0, 255, 0))
    corners_radius = params.IntSlider(min_val=1, max_val=50, default=1)
    corners_thickness = params.IntSlider(min_val=-1, max_val=20, default=-1)
    corners_line_type = params.ComboBox(
        options=list(cvc.LINES.keys()), options_map=cvc.LINES, default="8-Connected"
    )

    def draw(self, img_in, extra_in):
        """Draws points for CornerSubPix and its original contour points"""
        img = np.copy(img_in)
        if extra_in is None:
            return img

        good_features, corners = extra_in
        for x, y in good_features:
            cv2.circle(img, (x, y), self.good_feat_radius, self.good_feat_color, self.good_feat_thickness, cvc.LINES[self.good_feat_line_type])
        for x, y in corners:
            cv2.circle(img, (x, y), self.corners_radius, self.corners_color, self.corners_thickness, cvc.LINES[self.corners_line_type])
        return img


class ClusterGenerator(BaseTransform):
    """Generates clusters of points"""

    img_size = params.Dimensions2D(min_val=100, max_val=800, default=(250, 250))
    clusters = params.IntSlider(min_val=1, max_val=10, default=5)
    points_per_cluster = params.IntSlider(min_val=1, max_val=50, default=25)
    sigma = params.IntSlider(
        min_val=1,
        max_val=50,
        default=15,
        help_text="Sigma for gaussian spread from point centers",
    )

    def draw(self, img_in, extra_in):
        """Generates clusters of points"""
        points = self._generate_points()
        return img_in, points

    def _generate_points(self):
        """Generate random points for clusters"""
        points = []
        for _ in range(self.clusters):
            center = np.random.randint(0, self.img_size[0], 2)
            cluster_points = np.random.normal(center, self.sigma, (self.points_per_cluster, 2))
            points.append(cluster_points)
        return np.vstack(points)


class DrawKMeansPoints(BaseTransform):
    """Draws points for Kmeans"""

    point_size = params.IntSlider(min_val=1, max_val=25, default=2)
    center_point_size = params.IntSlider(min_val=1, max_val=25, default=4)
    center_color = params.ColorPicker(default=(0, 255, 0))
    h = params.IntSlider(
        min_val=0,
        max_val=179,
        default=100,
    )
    s = params.IntSlider(min_val=1, max_val=255, default=255)
    v = params.IntSlider(min_val=1, max_val=255, default=255)
    line_type = params.ComboBox(
        options=list(cvc.LINES.keys()), options_map=cvc.LINES, default="8-Connected"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def draw(self, img_out, extra_in):
        # Add safety check for None value
        if extra_in is None:
            return img_out  # Return the image without modifications
        
        points, labels, centers = extra_in
        img = np.copy(img_out)
        colors = self._get_colors(self.h, self.s, self.v, len(centers))
        for point, label in zip(points, labels):
            cv2.circle(img, tuple(point), self.point_size, colors[label[0]], cvc.LINES[self.line_type])
        for center in centers:
            cv2.circle(img, tuple(center), self.center_point_size, self.center_color, cvc.LINES[self.line_type])
        return img

    def _get_colors(self, h, s, v, n_colors):
        """Generate colors for the clusters"""
        colors = []
        for i in range(n_colors):
            hue = (h + i * 180 // n_colors) % 180
            color = cv2.cvtColor(np.uint8([[[hue, s, v]]]), cv2.COLOR_HSV2BGR)[0][0]
            colors.append(tuple(int(c) for c in color))
        return colors


class BitwiseAnd(BaseTransform):
    """Perform a cv2.bitwise_and"""

    def draw(self, img_in, extra_in):
        """Perform a cv2.bitwise_and"""
        return cv2.bitwise_and(img_in, extra_in)


class CvtColor(BaseTransform):
    """Convert from BGR to a different color space"""

    color_range = params.ComboBox(
        options=["BGR", "HSV", "LAB", "YUV"], options_map=cvc.COLOR_BGR2
    )

    def draw(self, img_in, extra_in):
        """Convert from BGR to a different color space"""
        return cv2.cvtColor(img_in, cvc.COLOR_BGR2[self.color_range])


class DisplayHarris(BaseTransform):
    """Displays top N points of Harris Corners"""

    top_n_points = params.IntSlider(
        min_val=1, max_val=1000, default=100, help_text="Show top N points"
    )
    point_color = params.ColorPicker(default=(0, 0, 255))

    def draw(self, img_in, extra_in):
        """Displays top N points of Harris Corners"""
        img = np.copy(img_in)
        top_points = self._get_top_points(extra_in, self.top_n_points)
        for x, y in top_points:
            cv2.circle(img, (x, y), 5, self.point_color, -1)
        return img

    def _get_top_points(self, values, n_points):
        """Get top N points based on Harris response"""
        flat = values.flatten()
        indices = np.argpartition(flat, -n_points)[-n_points:]
        indices = indices[np.argsort(-flat[indices])]
        return np.column_stack(np.unravel_index(indices, values.shape))


class BlankCanvas(BaseTransform):
    """Create a blank canvas"""

    img_shape = params.Dimensions2D(
        min_val=100, max_val=800, default=(250, 250), read_only=False
    )
    color = params.ColorPicker(default=(0, 0, 0))

    def draw(self, img_in, extra_in):
        """Create a blank canvas"""
        blank = np.zeros((self.img_shape[1], self.img_shape[0], 3), dtype=np.uint8)
        # Fill with specified color if not black
        if any(self.color):
            blank[:] = self.color
        return blank


class DrawContours(BaseTransform):
    color = params.ColorPicker(default=(0, 255, 0))
    contour_index = params.IntSlider(
        min_val=-1,
        max_val=1,
        step=1,
        default=-1,
        help_text="-1 -> All Contours, otherwise only draw specific contour",
    )
    thickness = params.IntSlider(
        min_val=-1,
        max_val=10,
        default=2,
        help_text="-1 -> Filled; otherwise draw lines at specified thickness",
    )
    line_type = params.ComboBox(
        options=["4-Connected", "8-Connected", "Anti Aliased"],
        options_map=cvc.LINES,
        default="8-Connected",
    )

    def draw(self, img_in, contours):
        """Draw contours on the image"""
        img = np.copy(img_in)
        cv2.drawContours(img, contours, self.contour_index, self.color, self.thickness, cvc.LINES[self.line_type])
        return img


class DrawGaussianKernel(BaseTransform):
    """Display Transform for GetGaussianKernel"""

    def draw(self, img_in, extra_in):
        """Display Transform for GetGaussianKernel"""
        kernel = extra_in
        img = np.zeros((kernel.shape[0], 1), dtype=np.uint8)
        for i, val in enumerate(kernel):
            img[i, 0] = val * 255
        return img


class DrawPyrDown(BaseTransform):
    """Display Transform for PyrDown"""

    def draw(self, img_in, extra_in):
        """Display Transform for PyrDown"""
        return extra_in[-1]


class DrawSplit(BaseTransform):
    """Display Transform for Split"""

    def draw(self, img_in, extra_in):
        """Display Transform for Split"""
        return extra_in


class DrawMerge(BaseTransform):
    """Display Transform for Merge"""

    def draw(self, img_in, extra_in):
        """Display Transform for Merge"""
        return extra_in
