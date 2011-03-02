# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

default:
	$(MAKE) -C luckylensing/libll
	mkdir -p examples/magpats

.PHONY: default
