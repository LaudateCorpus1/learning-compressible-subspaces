#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2021 Apple Inc. All Rights Reserved.
#
import args
import main

if __name__ == "__main__":
    args = args.quantized_args()
    main.train(args, "quantized")
