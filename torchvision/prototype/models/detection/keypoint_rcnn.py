from typing import Any, Optional

from torchvision.prototype.transforms import CocoEval

from ....models.detection.keypoint_rcnn import (
    _resnet_fpn_extractor,
    _validate_trainable_layers,
    KeypointRCNN,
    misc_nn_ops,
    overwrite_eps,
)
from .._api import WeightsEnum, Weights
from .._meta import _COCO_PERSON_CATEGORIES, _COCO_PERSON_KEYPOINT_NAMES
from .._utils import _deprecated_param, _deprecated_positional, _ovewrite_value_param
from ..resnet import ResNet50_Weights, resnet50


__all__ = [
    "KeypointRCNN",
    "KeypointRCNN_ResNet50_FPN_Weights",
    "keypointrcnn_resnet50_fpn",
]


_COMMON_META = {"categories": _COCO_PERSON_CATEGORIES, "keypoint_names": _COCO_PERSON_KEYPOINT_NAMES}


class KeypointRCNN_ResNet50_FPN_Weights(WeightsEnum):
    Coco_Legacy = Weights(
        url="https://download.pytorch.org/models/keypointrcnn_resnet50_fpn_coco-9f466800.pth",
        transforms=CocoEval,
        meta={
            **_COMMON_META,
            "recipe": "https://github.com/pytorch/vision/issues/1606",
            "box_map": 50.6,
            "kp_map": 61.1,
        },
    )
    Coco_V1 = Weights(
        url="https://download.pytorch.org/models/keypointrcnn_resnet50_fpn_coco-fc266e95.pth",
        transforms=CocoEval,
        meta={
            **_COMMON_META,
            "recipe": "https://github.com/pytorch/vision/tree/main/references/detection#keypoint-r-cnn",
            "box_map": 54.6,
            "kp_map": 65.0,
        },
    )
    default = Coco_V1


def keypointrcnn_resnet50_fpn(
    weights: Optional[KeypointRCNN_ResNet50_FPN_Weights] = None,
    progress: bool = True,
    num_classes: Optional[int] = None,
    num_keypoints: Optional[int] = None,
    weights_backbone: Optional[ResNet50_Weights] = None,
    trainable_backbone_layers: Optional[int] = None,
    **kwargs: Any,
) -> KeypointRCNN:
    if type(weights) == bool and weights:
        _deprecated_positional(kwargs, "pretrained", "weights", True)
    if "pretrained" in kwargs:
        default_value = KeypointRCNN_ResNet50_FPN_Weights.Coco_V1
        if kwargs["pretrained"] == "legacy":
            default_value = KeypointRCNN_ResNet50_FPN_Weights.Coco_Legacy
            kwargs["pretrained"] = True
        weights = _deprecated_param(kwargs, "pretrained", "weights", default_value)
    weights = KeypointRCNN_ResNet50_FPN_Weights.verify(weights)
    if type(weights_backbone) == bool and weights_backbone:
        _deprecated_positional(kwargs, "pretrained_backbone", "weights_backbone", True)
    if "pretrained_backbone" in kwargs:
        weights_backbone = _deprecated_param(
            kwargs, "pretrained_backbone", "weights_backbone", ResNet50_Weights.ImageNet1K_V1
        )
    weights_backbone = ResNet50_Weights.verify(weights_backbone)

    if weights is not None:
        weights_backbone = None
        num_classes = _ovewrite_value_param(num_classes, len(weights.meta["categories"]))
        num_keypoints = _ovewrite_value_param(num_keypoints, len(weights.meta["keypoint_names"]))
    else:
        if num_classes is None:
            num_classes = 2
        if num_keypoints is None:
            num_keypoints = 17

    trainable_backbone_layers = _validate_trainable_layers(
        weights is not None or weights_backbone is not None, trainable_backbone_layers, 5, 3
    )

    backbone = resnet50(weights=weights_backbone, progress=progress, norm_layer=misc_nn_ops.FrozenBatchNorm2d)
    backbone = _resnet_fpn_extractor(backbone, trainable_backbone_layers)
    model = KeypointRCNN(backbone, num_classes, num_keypoints=num_keypoints, **kwargs)

    if weights is not None:
        model.load_state_dict(weights.get_state_dict(progress=progress))
        if weights == KeypointRCNN_ResNet50_FPN_Weights.Coco_V1:
            overwrite_eps(model, 0.0)

    return model
