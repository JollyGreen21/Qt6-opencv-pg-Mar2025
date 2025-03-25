import copy
import logging
from typing import List, Dict, Any, Optional, Union

import numpy as np
from PySide6 import QtCore

log = logging.getLogger(__name__)


class Window(QtCore.QObject):
    image_updated = QtCore.Signal()

    counter = 1

    def __init__(self, transforms: List, name: str = ""):
        super().__init__()
        self.transforms = transforms
        self.index = None
        self.pipeline = None
        self.last_out = None
        self.last_in = None
        self.extra_in = None
        self.extra_out = None

        # Use a suitable name if none is provided
        if not name:
            self.name = f"Step {self.counter}"
            Window.counter += 1
        else:
            self.name = name

    @classmethod
    def reset_counter(cls):
        cls.counter = 1

    @classmethod
    def increment_counter(cls):
        cls.counter += 1

    @classmethod
    def decrement_counter(cls):
        cls.counter -= 1

    def set_pipeline(self, pipeline):
        self.pipeline = pipeline

    def get_name(self):
        return self.name

    def set_index(self, index):
        self.index = index

    def get_index(self):
        return self.index

    def get_transforms(self):
        return self.transforms

    def set_transforms(self, transforms):
        self.transforms = transforms

    def get_last_output(self):
        return self.last_out

    def get_last_input(self):
        return self.last_in

    def get_extra_input(self):
        return self.extra_in

    def get_extra_output(self):
        return self.extra_out

    def set_name(self, name):
        self.name = name

    def reset_transforms(self):
        self.transforms = []

    def clear_pipeline(self):
        self.pipeline = None

    def clear_last_output(self):
        self.last_out = None

    def clear_last_input(self):
        self.last_in = None

    def clear_extra_input(self):
        self.extra_in = None

    def clear_extra_output(self):
        self.extra_out = None

    def clear_all(self):
        self.clear_pipeline()
        self.clear_last_output()
        self.clear_last_input()
        self.clear_extra_input()
        self.clear_extra_output()
        self.reset_transforms()

    def update_name(self, prefix):
        self.name = f"{prefix} {self.name}"

    def reset_name(self):
        self.name = f"Step {Window.counter}"

    def reset_all(self):
        Window.reset_counter()
        self.reset_name()
        self.reset_transforms()
        self.clear_pipeline()
        self.clear_last_output()
        self.clear_last_input()
        self.clear_extra_input()
        self.clear_extra_output()

    def start_pipeline(self, transform_index: int = 0) -> None:
        """Runs pipeline from current window, starting on `transform_index`
        
        Args:
            transform_index (int): Index of transform to start from. Must be >= 0.
            
        Raises:
            ValueError: If transform_index is negative
            RuntimeError: If pipeline is not set
        """
        if transform_index < 0:
            raise ValueError(f"Transform index must be >= 0. Got {transform_index}")
            
        log.debug(
            "Starting Pipeline from Window %s, transform index: %s",
            self.index,
            transform_index,
        )
        if self.pipeline is None:
            log.warning("Pipeline is not set, cannot start pipeline")
            raise RuntimeError("Pipeline is not set, cannot start pipeline")
        
        if transform_index >= len(self.transforms):
            log.warning(
                f"Transform index {transform_index} out of range (max: {len(self.transforms)-1 if self.transforms else 0})"
            )
            return
            
        self.pipeline.run_pipeline(self.index, transform_index)

    def draw(self, img_in: Optional[np.ndarray], extra_in: Any, transform_index: int = 0) -> tuple:
        """Call _draw on each child transform in sequence and return final output"""
        if transform_index < 0:
            raise ValueError(f"Transform index must be >= 0. Got {transform_index}")

        if img_in is not None and len(img_in.shape) > 0:
            self.last_in = np.copy(img_in)
            img_out = np.copy(img_in)
            self.extra_in = copy.deepcopy(extra_in)
            extra_out = copy.deepcopy(extra_in)
        else:
            img_out = None
            extra_out = None
            self.last_in = None
            self.extra_in = None

        # Run the transforms
        for transform in self.transforms[transform_index:]:
            img_out, extra_out = transform._draw(img_out, extra_out)

        self.last_out = np.copy(img_out)
        self.extra_out = copy.deepcopy(extra_out)
        self.image_updated.emit()
        return img_out, extra_out
