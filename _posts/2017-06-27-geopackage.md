---
layout: post
title: Geopackage
date: 2017-06-27
summary: Rest In Peace shapefile
logo: map-marker
---

Last week Roger Bivand mentioned geopackage (abreviated GPKG) in a R-SIG-geo mailing list [post](http://r-sig-geo.2731867.n2.nabble.com/proj4string-read-by-readOGR-doesn-t-seem-to-precisely-specify-source-shapefile-projection-td7591243.html#a7591248) (by the way SIG stands for Special Interest Group, nothing to do with GIS in French ...).

Geopackage is an open file format to store geographical data in vector format (and apparently also raster format, but we'll focus on the vector part for now). The reason this caught my attention is that I have been looking for alternatives to shapefile for a long time. So I decided to investigate this gpkg format a bit; particularly how to read and write it with the R and python's main open source libraries, as well as QGIS.

It's no big news that the shapefile format has some serious limitations, starting with the fact that one file is in fact composed of at least 3 files (usually more), so that extreme caution is required when moving files around a computer or e-mailing them to someone to make sure all files stay together. Another, perhaps worse, characteristic of shapefiles is that field names are limited to 10 characters... yes, just 10!!! I can't recall how many times I've seen the warning message from `writeOGR` telling me that field names were being abreviated when writing a carefully crafted `Spatial*DataFrame` to shapefile; so frustrating!! I wouldn't call shapefile a nightmare but we're close...
But despite these limitations, shapefile is ubiquitus, we've all used it, and we almost all agree that it's the 'lingua franca' of the GIS world (as described by Tom MacWright in a rather old but still very informative [blog post](https://macwright.org/2012/10/31/gis-with-python-shapely-fiona.html)).

My previous attempts to find alternatives to shapefiles were not entirely successful. I tried [spatialite](https://en.wikipedia.org/wiki/SpatiaLite) a few years ago, but faced some limitations when trying to write multiple layers to a single file. Another limitation of spatialite is its weight; an empty spatialite database will take about 6MB of disk space; not exactly my definition of lightweight. And at the end I was left telling people that shapefiles were bad but without being able to propose any reasonable alternative. The word *reasonable* is important here as not everyone wants to setup a postGIS database to visualize a bunch of GPS points. An ideal format would be lightweight and easy to use for non GIS specialist; and GPKG appears to fulfill that role perfectly.

So let's see how it plays with the tools I usually use to read, write and manipulate vector data. First python and then R.

## Python

Fiona is probably the most pythonic library for reading and writing geospatial vector data, and that's what I will use in the example below. It works with dictionary representations of features which can be written to geospatial files almost as easily as it is to write to a text file. It obviously buids on top of OGR. Note that fiona is not the only way to read and write geospatial vector data; geopandas is a very interesting project as well which can do as much with a slightly different data structure and philosophy.

> Note: fiona may come in the form of a binary wheel when installed with pip. This means that it comes with its own version of gdal/OGR, to which it is statically linked. Unfortuanlly the binaries that come with the current fiona version (1.7.7) do not include the geopackage driver. It might therefore be necessary to install fiona from source in order to allow it to dynamically link to the system gdal. This can be done with `pip install -I fiona --no-binary fiona`.

The code below, query the coordinates of some cities where I've lived (I admit selecting only those with a non ambiguous name, ... no spaces, accents or dashes), builds the features and writes them to a geopackage file.

```python
from pprint import pprint
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
with fiona.open('/home/loic/sandbox/cities.gpkg', 'w',
                layer='cities_points',
                driver='GPKG',
                schema=schema,
                crs=crs) as dst:
    for city in cities:
        feature = feature_from_name(city)
        dst.write(feature)
```




Some conclusion points:

- geopackage is a very convenient, lightweight geospatial vector data format that does not have any of the limitation of the shapefiles.
- It works well with GIS tools (python and R libraries, QGIS, and ArcGIS)
- `writeOGR` does not handle the creation of multilayer geopackage files (though one file per layer is still much better than what shapefiles have to offer)

After these tests I can not longer find any good reason to keep using shapefiles. Do you?