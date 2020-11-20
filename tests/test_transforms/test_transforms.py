"""Excercise transforms to ensure they don't cause exceptions

The goal here is to hopefully catch API changes in future versions by running
the transforms to see if sane values cause exceptions

Assumes we're testing the little robot.png included with the package
"""
from unittest import mock
from pkg_resources import resource_filename

import numpy as np
import cv2

import pytest

from opencv_pg import transforms
from opencv_pg.models import cv2_constants as cvc
from opencv_pg.models.transform_windows import get_transform_window


IMG_PATH = resource_filename('opencv_pg', 'robot.jpg')


def _check_error(window):
    """Assert error is None for each Transform"""
    for tf in window.transforms:
        assert tf.error is None


def _test_single_attr(transform, attr, value):
    """Tests setting single attribute and running pipeline"""
    # Given
    window = get_transform_window(transform, IMG_PATH)
    tf = window.transforms[1]
    setattr(tf, attr, value)

    # When
    window.draw(None, None)

    # Then
    _check_error(window)


class TestGaussianBlur():
    @pytest.mark.parametrize(
        'border_type',
        list(transforms.GaussianBlur.border_type.options)
    )
    def test_border_type_combos(self, border_type):
        """Test various border types"""
        # Given
        window = get_transform_window(transforms.GaussianBlur, IMG_PATH)
        tf = window.transforms[1]

        # Some reasonable defaults
        tf.k_size_x = 21
        tf.k_size_y = 21
        tf.sigma_x = 5
        tf.sigma_y = 5
        tf.border_type = cvc.BORDERS[border_type]

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestMedianBlur():
    @pytest.mark.parametrize('value', (1, 51, 99))
    def test_various_values(self, value):
        # Given
        window = get_transform_window(transforms.MedianBlur, IMG_PATH)
        tf = window.transforms[1]
        tf.k_size = value

        # When
        window.draw(None, None)

        # Then
        assert tf.error is None


@mock.patch('opencv_pg.models.transforms.CopyMakeBorder.update_widgets_state', lambda x: None)
class TestCopyMakeBorder():
    @pytest.mark.parametrize(
        'border_type',
        list(transforms.CopyMakeBorder.border_type.options)
    )
    def test_border_types(self, border_type):
        """Test border types"""
        _test_single_attr(
            transforms.CopyMakeBorder,
            'border_type',
            cvc.BORDERS[border_type]
        )

    @pytest.mark.parametrize('value', (0, 15))
    def test_min_and_middle_val(self, value):
        # Given
        window = get_transform_window(transforms.CopyMakeBorder, IMG_PATH)
        tf = window.transforms[1]
        tf.top = value
        tf.right = value
        tf.bottom = value
        tf.left = value

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


@mock.patch('opencv_pg.models.transforms.Normalize.update_widgets_state', lambda x: None)
class TestNormalize():
    @pytest.mark.parametrize('alpha, beta', (
        (0, 0),
        (0, 255),
        (125, 125),
        (255, 0),
        (255, 255),
    ))
    def test_minmax(self, alpha, beta):
        # Given
        window = get_transform_window(transforms.Normalize, IMG_PATH)
        tf = window.transforms[1]
        tf.alpha = alpha
        tf.beta = beta
        tf.norm_type = cvc.NORMS['NORM_MINMAX']

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    @pytest.mark.parametrize('alpha', (0, 125, 255))
    def test_norm_inf(self, alpha):
        # Given
        window = get_transform_window(transforms.Normalize, IMG_PATH)
        tf = window.transforms[1]
        tf.alpha = alpha
        tf.norm_type = cvc.NORMS['NORM_INF']

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    @pytest.mark.parametrize('alpha', (0, 275400000 // 2, 275400000))
    def test_l1(self, alpha):
        # Given
        window = get_transform_window(transforms.Normalize, IMG_PATH)
        tf = window.transforms[1]
        tf.alpha = alpha
        tf.norm_type = cvc.NORMS['NORM_L1']

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    @pytest.mark.parametrize('alpha', (0, 7735580382 // 2, 7735580382))
    def test_l2(self, alpha):
        # Given
        window = get_transform_window(transforms.Normalize, IMG_PATH)
        tf = window.transforms[1]
        tf.alpha = alpha
        tf.norm_type = cvc.NORMS['NORM_L2']

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestSplit():
    def test_split(self):
        """No parameters here"""
        # Given
        window = get_transform_window(transforms.Split, IMG_PATH)

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestMerge():
    def test_merge(self):
        """No parameters here"""
        # Given
        window = get_transform_window(transforms.Split, IMG_PATH)

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestFilter2D():
    @pytest.mark.parametrize(
        'border_type',
        list(transforms.Filter2D.border_type.options)
    )
    def test_border_types(self, border_type):
        """Test border types"""
        _test_single_attr(
            transforms.Filter2D,
            'border_type',
            cvc.BORDERS[border_type]
        )

    @pytest.mark.parametrize('value', (0, 100, 300))
    def test_delta_values(self, value):
        # Given
        window = get_transform_window(transforms.Filter2D, IMG_PATH)
        tf = window.transforms[1]
        tf.delta = value

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    @pytest.mark.parametrize('rows, cols', (
        (1, 1),
        (3, 1),
        (1, 3),
        (3, 3),
    ))
    def test_kernel_sizes(self, rows, cols):
        # Given
        window = get_transform_window(transforms.Filter2D, IMG_PATH)
        tf = window.transforms[1]
        tf.kernel = np.ones((rows, cols))

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    @pytest.mark.parametrize('value', (
        np.array([[1, 1], [1, 1]]),
        np.array([[1, 0], [0, 0]]),
        np.array([[0, 0], [0, 0]]),
    ))
    def test_kernel_values(self, value):
        # Given
        window = get_transform_window(transforms.Filter2D, IMG_PATH)
        tf = window.transforms[1]
        tf.kernel = value

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    @pytest.mark.parametrize('row, col', (
        (-1, -1),
        (0, 0),
        (2, 2),
        (0, 2),
        (2, 0),
    ))
    def test_anchors(self, row, col):
        # Given
        window = get_transform_window(transforms.Filter2D, IMG_PATH)
        tf = window.transforms[1]
        tf.kernel = np.ones((3, 3))
        tf._kernel.anchor = (row, col)

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestCanny():
    @pytest.mark.parametrize('thresh1, thresh2, aperture, l2_grad', (
        (0, 0, 3, False),
        (0, 0, 3, False),
        (200, 200, 5, False),
        (200, 200, 5, True),
        (1000, 1000, 7, True),
    ))
    def test_canny(self, thresh1, thresh2, aperture, l2_grad):
        # Given
        window = get_transform_window(transforms.Canny, IMG_PATH)
        tf = window.transforms[1]
        tf.threshold1 = thresh1
        tf.threshold2 = thresh2
        tf.aperture_size = aperture
        tf.use_l2_gradient = l2_grad

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestHoughLines():
    def test_defaults(self):
        """Test using the defaults for all transforms"""
        # Given
        window = get_transform_window(transforms.HoughLines, IMG_PATH)

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    def test_reasonable_values(self):
        """Test using some reasonable values to reduce lines found"""
        # Given
        window = get_transform_window(transforms.HoughLines, IMG_PATH)
        gauss, canny, hough = window.transforms[1:4]

        # Set reasonable values for
        gauss.k_size_x = 9
        gauss.k_size_y = 9
        gauss.sigma_x = 2

        canny.threshold1 = 185
        canny.threshold2 = 120
        canny.aperture_size = 3
        canny.use_l2_gradient = True

        hough.rho = 23
        hough.theta = 0.7
        hough.min_theta = 1.4
        hough.max_theta = 1.85

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestHoughLinesP():
    def test_defaults(self):
        """Test using the defaults for all transforms"""
        # Given
        window = get_transform_window(transforms.HoughLinesP, IMG_PATH)

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    def test_reasonable_values(self):
        """Test using some reasonable values to reduce lines found"""
        # Given
        window = get_transform_window(transforms.HoughLinesP, IMG_PATH)
        gauss, canny, hough = window.transforms[1:4]

        # Set reasonable values for
        gauss.k_size_x = 9
        gauss.k_size_y = 9
        gauss.sigma_x = 2

        canny.threshold1 = 185
        canny.threshold2 = 120
        canny.aperture_size = 3
        canny.use_l2_gradient = True

        hough.rho = 159
        hough.theta = 1.38
        hough.threshold = 36
        hough.min_length = 160
        hough.max_gap = 59

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


@mock.patch('opencv_pg.models.transforms.HoughCircles.update_widgets_state', lambda x: None)
class TestHoughCircles():
    def test_defaults(self):
        """Test using the defaults for all transforms"""
        # Given
        window = get_transform_window(transforms.HoughCircles, IMG_PATH)

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    def test_reasonable_values(self):
        """Test using some reasonable values to reduce lines found"""
        # Given
        window = get_transform_window(transforms.HoughCircles, IMG_PATH)
        gauss, hough = window.transforms[1:3]

        # Set reasonable values for
        gauss.k_size_x = 9
        gauss.k_size_y = 9
        gauss.sigma_x = 2

        hough.min_dist = 50
        hough.param1 = 35
        hough.param2 = 20
        hough.min_radius = 7
        hough.max_radius = 39

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


@mock.patch('opencv_pg.models.transforms.Dilate.update_widgets_state', lambda x: None)
class TestDilate():
    @pytest.mark.parametrize(
        'border_type',
        list(transforms.Dilate.border_type.options))
    def test_border_types(self, border_type):
        """Test the different border options"""
        # Given
        window = get_transform_window(transforms.Dilate, IMG_PATH)
        tf = window.transforms[1]
        tf.iterations = 5
        tf.border_type = cvc.BORDERS[border_type]
        tf.border_val = (255, 255, 255)
        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    @pytest.mark.parametrize('kernel, anchor, iterations', (
        (cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1)), (-1, -1), 1),
        (cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), (-1, -1), 1),
        (cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)), (-1, -1), 1),
        (cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), (-1, -1), 1),
        (cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), (-1, -1), 100),
        (cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), (0, 0), 1),
        (cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), (2, 2), 1),
        (cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), (2, 2), 5),
    ))
    def test_other_params(self, kernel, anchor, iterations):
        """Test combinations of the other params"""
        # Given
        window = get_transform_window(transforms.Dilate, IMG_PATH)
        tf = window.transforms[1]
        tf.iterations = iterations
        tf.kernel = kernel
        tf._kernel.anchor = anchor

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestBilateralFilter():
    @pytest.mark.parametrize(
        'border_type',
        list(transforms.BilateralFilter.border_type.options))
    def test_border_types(self, border_type):
        """Test the different border options"""
        _test_single_attr(
            transforms.BilateralFilter,
            'border_type',
            cvc.BORDERS[border_type]
        )

    # NOTE: Not testing 0 diam b/c it's an auto and takes forever
    @pytest.mark.parametrize('diameter, sigma_c, sigma_s', (
        (1, 85, 85),
        (12, 85, 85),
        (12, 0, 0),
    ))
    def test_other_params(self, diameter, sigma_c, sigma_s):
        """Test combinations of the other params"""
        # Given
        window = get_transform_window(transforms.BilateralFilter, IMG_PATH)
        tf = window.transforms[1]
        tf.d = diameter
        tf.sigma_color = sigma_c
        tf.sigma_space = sigma_s

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestSobel():

    @pytest.mark.parametrize(
        'border_type',
        list(transforms.Sobel.border_type.options)
    )
    def test_border_types(self, border_type):
        """Test the different border options"""
        # Given
        window = get_transform_window(transforms.Sobel, IMG_PATH)
        tf = window.transforms[1]
        tf.border_type = cvc.BORDERS[border_type]

        # When
        window.draw(None, None)

        # Then
        _check_error(window)

    @pytest.mark.parametrize('dx, dy, k_size, scale, delta', (
        (1, 1, 1, .1, -255),
        (1, 1, 1, .1, 255),
        (2, 2, 3, 200, 255),
        (2, 2, 5, 100, 0),
        (2, 2, 7, 100, 0),
        (1, 1, 7, .1, 0),
    ))
    def test_other_params(self, dx, dy, k_size, scale, delta):
        """Test other param combinations"""
        # Given
        window = get_transform_window(transforms.Sobel, IMG_PATH)
        tf = window.transforms[1]
        tf.dx = dx
        tf.dy = dy
        tf.k_size = k_size
        tf.scale = scale
        tf.delta = delta

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


@mock.patch('opencv_pg.models.transforms.Remap.update_widgets_state', lambda x: None)
class TestRemap():

    @pytest.mark.parametrize(
        'border_type',
        list(transforms.Remap.border_type.options)
    )
    def test_border_types(self, border_type):
        """Test the different border options"""
        _test_single_attr(
            transforms.Remap,
            'border_type',
            cvc.BORDERS[border_type]
        )

    @pytest.mark.parametrize(
        'interp_type',
        list(transforms.Remap.interpolation_type.options)
    )
    def test_interpolation_types(self, interp_type):
        """Test the different interpolation options"""
        _test_single_attr(
            transforms.Remap,
            'interpolation_type',
            cvc.INTERPOLATION[interp_type]
        )

    @pytest.mark.parametrize('r, theta', (
        (1, 1),
        (30, 20),
    ))
    def test_other_params(self, r, theta):
        """Test other param combinations"""
        # Given
        window = get_transform_window(transforms.Remap, IMG_PATH)
        tf = window.transforms[1]
        tf.r = r
        tf.theta = theta

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


@mock.patch('opencv_pg.models.transforms.SepFilter2D.update_widgets_state', lambda x: None)
class TestSepFilter2D():

    @pytest.mark.parametrize(
        'border_type',
        list(transforms.SepFilter2D.border_type.options)
    )
    def test_border_types(self, border_type):
        """Test the different border options"""
        _test_single_attr(
            transforms.SepFilter2D,
            'border_type',
            cvc.BORDERS[border_type]
        )

    @pytest.mark.skip(reason="Broken")
    @pytest.mark.parametrize('kernel_x, kernel_y, delta', (
        (np.ones((1, 1)), np.ones((1, 5)), 0),
        (np.ones((1, 5)), np.ones((1, 1)), 0),
        (np.ones((1, 1)), np.ones((1, 1)), 0),
        (np.ones((1, 3)), np.ones((1, 3)), -255),
        (np.ones((1, 3)), np.ones((1, 3)), 255),
    ))
    def test_other_params(self, kernel_x, kernel_y, delta):
        """Test other param combinations"""
        # Given
        window = get_transform_window(transforms.Remap, IMG_PATH)
        tf = window.transforms[1]
        tf.kernel_X = kernel_x
        tf.kernel_Y = kernel_y
        tf.delta = delta

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


@mock.patch('opencv_pg.models.transforms.BoxFilter.interconnect_widgets', lambda x: None)
class TestBoxFilter():

    @pytest.mark.parametrize(
        'border_type',
        list(transforms.BoxFilter.border_type.options)
    )
    def test_border_types(self, border_type):
        """Test the different border options"""
        _test_single_attr(
            transforms.SepFilter2D,
            'border_type',
            cvc.BORDERS[border_type]
        )

    @pytest.mark.parametrize('kernel, normalize', (
        (np.ones((1, 1)), False),
        (np.ones((1, 1)), True),
        (np.ones((3, 3)), False),
        (np.ones((3, 3)), True),
        (np.ones((1, 3)), True),
        (np.ones((3, 1)), True),
        (np.ones((1, 3)), False),
        (np.ones((3, 1)), False),
    ))
    def test_other_params(self, kernel, normalize):
        """Test other param combinations"""
        # Given
        window = get_transform_window(transforms.BoxFilter, IMG_PATH)
        tf = window.transforms[1]
        tf.kernel = kernel
        tf.normalize = normalize

        # When
        window.draw(None, None)

        # Then
        _check_error(window)


class TestFastNIMeansDenoisingColored():

    @pytest.mark.parametrize('temp_win_size, search_win_size, h, h_color', (
        (1, 1, 3, 7),
        (7, 3, 3, 7),  # window smaller than template
        (7, 21, 3, 7),
        (15, 51, 3, 7),
        (7, 21, 0, 0),
        (7, 21, 25, 0),
        (7, 21, 0, 25),
        (7, 21, 25, 25),
    ))
    def test_other_params(self, temp_win_size, search_win_size, h, h_color):
        """Test other param combinations"""
        # Given
        window = get_transform_window(transforms.FastNIMeansDenoisingColored, IMG_PATH)
        tf = window.transforms[1]
        tf.template_window_size = temp_win_size
        tf.search_window_size = search_win_size
        tf.h = h
        tf.h_color = h_color

        # When
        window.draw(None, None)

        # Then
        _check_error(window)
