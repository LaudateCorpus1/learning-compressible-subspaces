#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2021 Apple Inc. All Rights Reserved.
#
import torch.nn as nn


# BasicBlock {{{
class BasicBlock(nn.Module):
    M = 2
    expansion = 1

    def __init__(
        self,
        builder,
        inplanes,
        planes,
        stride=1,
        downsample=None,
        base_width=64,
    ):
        super(BasicBlock, self).__init__()
        if base_width / 64 > 1:
            raise ValueError("Base width >64 does not work for BasicBlock")

        self.conv1 = builder.conv3x3(inplanes, planes, stride)
        self.bn1 = builder.batchnorm(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = builder.conv3x3(planes, planes)
        self.bn2 = builder.batchnorm(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        if self.bn1 is not None:
            out = self.bn1(out)

        out = self.relu(out)

        out = self.conv2(out)

        if self.bn2 is not None:
            out = self.bn2(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


# BasicBlock }}}

# Bottleneck {{{
class Bottleneck(nn.Module):
    M = 3
    expansion = 4

    def __init__(
        self,
        builder,
        inplanes,
        planes,
        stride=1,
        downsample=None,
        base_width=64,
    ):
        super(Bottleneck, self).__init__()
        width = int(planes * base_width / 64)
        self.conv1 = builder.conv1x1(inplanes, width)
        self.bn1 = builder.batchnorm(width)
        self.conv2 = builder.conv3x3(width, width, stride=stride)
        self.bn2 = builder.batchnorm(width)
        self.conv3 = builder.conv1x1(width, planes * self.expansion)
        self.bn3 = builder.batchnorm(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual

        out = self.relu(out)

        return out


# Bottleneck }}}

# ResNet {{{
class ResNet(nn.Module):
    def __init__(
        self,
        builder,
        block_builder,
        block,
        layers,
        num_classes=1000,
        base_width=64,
    ):
        self.inplanes = 64
        super(ResNet, self).__init__()

        self.base_width = base_width
        if self.base_width // 64 > 1:
            print(f"==> Using {self.base_width // 64}x wide model")

        self.conv1 = builder.conv7x7(3, 64, stride=2, first_layer=True)

        self.bn1 = builder.batchnorm(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block_builder, block, 64, layers[0])
        self.layer2 = self._make_layer(
            block_builder, block, 128, layers[1], stride=2
        )
        self.layer3 = self._make_layer(
            block_builder, block, 256, layers[2], stride=2
        )
        self.layer4 = self._make_layer(
            block_builder, block, 512, layers[3], stride=2
        )
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.return_feats = False

        self.fc = builder.conv1x1(
            512 * block.expansion, num_classes, last_layer=True
        )

    def _make_layer(self, builder, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            dconv = builder.conv1x1(
                self.inplanes, planes * block.expansion, stride=stride
            )
            dbn = builder.batchnorm(planes * block.expansion)
            if dbn is not None:
                downsample = nn.Sequential(dconv, dbn)
            else:
                downsample = dconv

        layers = []
        layers.append(
            block(
                builder,
                self.inplanes,
                planes,
                stride,
                downsample,
                base_width=self.base_width,
            )
        )
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(
                block(
                    builder, self.inplanes, planes, base_width=self.base_width
                )
            )

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)

        if self.bn1 is not None:
            x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        feats = self.avgpool(x)
        x = self.fc(feats)
        x = x.view(x.size(0), -1)

        if self.return_feats:
            return x, feats.view(feats.size(0), -1)
        return x


def _get_output_size(dataset: str):
    return {
        "cifar10": 10,
        "imagenet": 1000,
    }[dataset]


# ResNet }}}
def ResNet18(builder, block_builder, dataset):
    return ResNet(
        builder,
        block_builder,
        BasicBlock,
        [2, 2, 2, 2],
        _get_output_size(dataset),
    )
