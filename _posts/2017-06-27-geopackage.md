---
layout: post
title: Geopackage
date: 2017-06-27
summary: RIP shapefile
logo: map-marker
---

Last week Roger Bivand mentioned geopackage (abreviated GPKG) in a R-SIG-geo mailing list [post](http://r-sig-geo.2731867.n2.nabble.com/proj4string-read-by-readOGR-doesn-t-seem-to-precisely-specify-source-shapefile-projection-td7591243.html#a7591248) (by the way SIG stands for Special Interest Group, nothing to do with GIS in French ...).

Geopackage is an open file format to store geographical data in vector format (and apparently also raster format, but we'll focus on the vector part for now). The reason this caught my attention is that I have been looking for alternatives to shapefile for a long time. So I decided to investigate this gpkg format a bit; particularly how to read and write it with the R and python's main open source libraries, as well as QGIS.

It's no big news that the shapefile format has some serious limitations, starting with the fact that one file is in fact composed of at least 3 files (usually more); a very inconveninent characteristic when you want to move things around or e-mail data to someone. Imagine if you would buy sliced bred without any packaging to keep it together, that wouldn't be very convenient to carry it back home, would it?
Another, perhaps worse, characteristic of shapefiles is that field names (the names of the columns of the 'attribute table') are limited to 10 characters... yes, just 10!!! I can't recall how many times I've seen the warning message from `writeOGR` telling me that field names were being abreviated when writing a carefully crafted `Spatial*DataFrame` (`*` being any of `Lines`, `Polygons`, or `Points`) to shapefile; so frustrating!! I wouldn't call shapefile a nightmare but we're close...
But despite these limitations, shapefile is ubiquitus, we've all used it, and we almost all agree that it's the 'lingua franca' of the GIS world (as described by Tom MacWright in a rather old but still very informative [blog post](https://macwright.org/2012/10/31/gis-with-python-shapely-fiona.html)).

My previous attempts to find alternatives to shapefiles were not entirely successful. I tried [spatialite](https://en.wikipedia.org/wiki/SpatiaLite) a few years ago, but faced some limitations when trying to write multiple layers to a single file. Another limitation of spatialite is its weight; an empty spatialite database will take about 6MB of disk space; not exactly my definition of lightweight. And at the end I was left telling people that shapefiles were bad but without being able to propose any reasonable alternative. The word *reasonable* is important here as not everyone wants to setup a postGIS database to visualize a bunch of GPS points. An ideal format would be lightweight, self contained, and easy to use for non GIS specialist. GPKG appears to fulfill that role perfectly!

So let's see how it plays with the tools I usually use to read, write and manipulate vector data. First python and then R.

## Python

Fiona is probably the most pythonic library for reading and writing geospatial vector data, and that's what I will use in the example below. When using fiona, you have to work with dictionary representations of your features and these can be written to geospatial files almost as easily as it is to write a string to a text file. OGR is obviously the key workhose that works in the background for that to happen. Note that fiona is not the only way to read and write geospatial vector data; geopandas is a very interesting project as well which can do as much with a slightly different data structure and philosophy.

> Note: fiona may come in the form of a binary wheel when installed with pip. This means that it comes with its own version of gdal/OGR, to which it is statically linked. Unfortuanlly the binaries that come with the current fiona version (1.7.7) do not include the geopackage driver. It might therefore be necessary to install fiona from source in order to allow it to dynamically link to your system gdal. This can be done with `pip install -I fiona --no-binary fiona`.

The code below, query the coordinates of some cities where I've lived (I admit selecting only those with a non ambiguous name, ... no spaces, accents or dashes), builds the features and writes them to a geopackage file.

```python
import fiona
from fiona.crs import from_string
import requests

# Some city where I've lived
cities = ['rompon', 'angers', 'wageningen']

# To write data with fiona, we first have to define a schema, and the crs, that
# we'll pass as arguments when opening the connection to the file.
# After that, features are added one by one by writting a dictionary representation
# of that feature.
schema = {'geometry': 'Point',
          'properties': [('name', 'str'),
                         ('country', 'str')]}

crs = from_string('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

# Feature builder
def feature_from_name(city):
    r = requests.get("https://maps.googleapis.com/maps/api/geocode/json",
                     params={'address': city})
    coord = r.json()['results'][0]['geometry']['location']
    geometry = {'type': 'Point', 'coordinates': [coord['lng'], coord['lat']]}
    country = r.json()['results'][0]['address_components'][3]['long_name']
    feature = {'geometry': geometry,
               'properties': {'name': city,
                              'country': country}}
    return feature


# Open connection with gpkg file in a context manager and write features to it
with fiona.open('/home/loic/sandbox/cities_fiona.gpkg', 'w',
                layer='points',
                driver='GPKG',
                schema=schema,
                crs=crs) as dst:
    for city in cities:
        feature = feature_from_name(city)
        dst.write(feature)
```

We can verify that the features were properly written by running `ogrinfo`

```sh
ogrinfo cities_fiona.gpkg

# INFO: Open of `cities_fiona.gpkg'
#       using driver `GPKG' successful.
# 1: points (Point)

# And to get the layer specific information
ogrinfo cities_fiona.gpkg points

# Layer name: points
# Geometry: Point
# Feature Count: 3
# Extent: (-0.563166, 44.781400) - (5.665390, 51.969200)
# Layer SRS WKT:
# GEOGCS["WGS 84",
#     DATUM["WGS_1984",
#         SPHEROID["WGS 84",6378137,298.257223563,
#             AUTHORITY["EPSG","7030"]],
#         AUTHORITY["EPSG","6326"]],
#     PRIMEM["Greenwich",0,
#         AUTHORITY["EPSG","8901"]],
#     UNIT["degree",0.0174532925199433,
#         AUTHORITY["EPSG","9122"]],
#     AUTHORITY["EPSG","4326"]]
# FID Column = fid
# Geometry Column = geom
# name: String (0.0)
# country: String (0.0)
# OGRFeature(points):1
#   name (String) = rompon
#   country (String) = France
#   POINT (4.7174062 44.7813992)

# OGRFeature(points):2
#   name (String) = angers
#   country (String) = France
#   POINT (-0.563166 47.478419)

# OGRFeature(points):3
#   name (String) = wageningen
#   country (String) = Netherlands
#   POINT (5.6653948 51.9691868)
```

That's already great but geopackage is supposed to be able to handle multiple layer. So let's try to build another layer with a different geometry type and write it to the same file.

```python
import fiona
import pyproj
from shapely.geometry import Point, mapping

file_name = '/home/loic/sandbox/cities_fiona.gpkg'

# Define afunction that can build a buffer feature from a point feature
# The different steps for that are:
# - Define a local equidistant coordinate reference system
# - Build a Point geometry in that coordinate reference system
# - Make a buffer around the point
# - Create a dictionary representation of the polygon geometry
# - Reproject the polygon back to the original coordinate reference system
def buffer_from_point_feature(feature, distance):
    prj = pyproj.Proj(proj='aeqd', lat_0=feature['geometry']['coordinates'][0],
                      lon_0=feature['geometry']['coordinates'][1])
    geom = Point(prj(*feature['geometry']['coordinates']))
    buffer = geom.buffer(distance)
    feature_out = {'geometry': mapping(buffer),
                   'properties': feature['properties']}
    x_ll, y_ll = prj(*zip(*feature_out['geometry']['coordinates'][0]), inverse=True)
    coord_ll = []
    coord_ll.append(zip(x_ll, y_ll))
    feature_out['geometry']['coordinates'] = coord_ll
    return feature_out


# Read the data back
with fiona.open(file_name, layer = 'points') as src:
    buffer_collection = [buffer_from_point_feature(x, 1000) for x in src]
    schema = src.schema
    crs = src.crs


schema.update(geometry='Polygon')

with fiona.open(file_name, 'w', layer='polygons', driver='GPKG',
                schema=schema, crs=crs) as dst:
    for feature in buffer_collection:
        dst.write(feature)
```


Some conclusion points:

- geopackage is a very convenient, lightweight geospatial vector data format that does not have any of the limitation of the shapefiles.
- It works well with GIS tools (python and R libraries, QGIS, and ArcGIS)
- `writeOGR` does not handle the creation of multilayer geopackage files (though one file per layer is still much better than what shapefiles have to offer)
- Writing this post took longer than expected

After these tests I can not longer find any good reason to keep using shapefiles. Do you?