---
layout: post
title: lsru rewrite
date: 2018-10-28
summary: Python package for ordering and downloading Landsat surface reflectance data
logo: cloud-download
---

The past week I worked on a full re-write of `lsru` (Landsat Surface Reflectance Utils), a python package to order, query and download Landsat surface reflectance data.

Unprocessed Landsat data (Top of atmosphere radiance) can be downloaded directly without the need to place an order; manually or using packages like [Landsat-util](https://github.com/developmentseed/landsat-util). Surface reflectance refers to data that have been corrected for atmospheric effects; one way to obtain surface reflectance Landsat data is via the [ESPA](https://espa.cr.usgs.gov/) on demand pre-processing platform. It is what `lsru` helps you do, programmatically, from python. 


The initial version I had written for a rather specific research project of my friend Simon was mostly command line oriented, without a really usable API, and broke a long time ago when the USGS changed its naming conventions for Landsat with the release of collection 1. I therefore decided to give it a complete overhaul.


The new version of *lsru* has a fully functional and documented API, [online documentation](https://lsru.readthedocs.io/en/latest/), support both python 2 and 3, and can be installed directly from [pypi](https://pypi.org/project/lsru/0.4.0/) (`pip install lsru`).

Its features are:

- Query the USGS catalog (spatio-temporal window with various optional filters) using the `Usgs` class
- Place pre-processing orders to the ESPA platform for a list of scenes using the `Espa` class
- Handling ESPA orders status monitoring and download with the `Order` class
- A few helpers to help e.g. placing orders using a polygon, downloading data, etc

If you use it and discover a bug or think of additional features don't hesitate to let me know by raising an issue on [github](https://github.com/loicdtx/lsru) or by sending me an e-mail. 
